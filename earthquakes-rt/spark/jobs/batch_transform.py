# Batch transform: read bronze JSON snapshots, normalize, type-cast, write Parquet (silver),
# and upsert latest events into Postgres (gold).
#
# Run with:
# spark-submit --master spark://spark-master:7077 /opt/spark-apps/jobs/batch_transform.py

from pyspark.sql import SparkSession, functions as F, types as T
from datetime import datetime
import os
from common import get_env, silver_path

def build_spark():
    return (
        SparkSession.builder
        .appName("earthquakes-batch-transform")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

def schema_geojson():
    # Minimal schema for USGS GeoJSON feed
    return T.StructType([
        T.StructField("type", T.StringType()),
        T.StructField("metadata", T.StructType([
            T.StructField("generated", T.LongType()),
            T.StructField("url", T.StringType()),
            T.StructField("title", T.StringType()),
            T.StructField("count", T.IntegerType()),
        ])),
        T.StructField("features", T.ArrayType(T.StructType([
            T.StructField("type", T.StringType()),
            T.StructField("properties", T.StructType([
                T.StructField("mag", T.DoubleType()),
                T.StructField("place", T.StringType()),
                T.StructField("time", T.LongType()),
                T.StructField("updated", T.LongType()),
                T.StructField("tz", T.IntegerType()),
                T.StructField("url", T.StringType()),
                T.StructField("detail", T.StringType()),
                T.StructField("felt", T.IntegerType()),
                T.StructField("cdi", T.DoubleType()),
                T.StructField("mmi", T.DoubleType()),
                T.StructField("alert", T.StringType()),
                T.StructField("status", T.StringType()),
                T.StructField("tsunami", T.IntegerType()),
                T.StructField("sig", T.IntegerType()),
                T.StructField("net", T.StringType()),
                T.StructField("code", T.StringType()),
                T.StructField("ids", T.StringType()),
                T.StructField("sources", T.StringType()),
                T.StructField("types", T.StringType()),
                T.StructField("nst", T.IntegerType()),
                T.StructField("dmin", T.DoubleType()),
                T.StructField("rms", T.DoubleType()),
                T.StructField("gap", T.DoubleType()),
                T.StructField("magType", T.StringType()),
                T.StructField("type", T.StringType()),
                T.StructField("title", T.StringType()),
            ])),
            T.StructField("geometry", T.StructType([
                T.StructField("type", T.StringType()),
                T.StructField("coordinates", T.ArrayType(T.DoubleType())),  # [lon, lat, depth_km]
            ])),
            T.StructField("id", T.StringType()),
        ]))),
        T.StructField("bbox", T.ArrayType(T.DoubleType())),
    ])

def flatten(df):
    # Explode features -> one row per event
    fdf = df.select(F.explode("features").alias("f"))
    # Coordinates are [lon, lat, depth_km]
    return fdf.select(
        F.col("f.id").alias("event_id"),
        F.col("f.properties.time").alias("time_ms"),
        F.col("f.properties.updated").alias("updated_ms"),
        F.col("f.properties.mag").alias("magnitude"),
        F.col("f.properties.magType").alias("mag_type"),
        F.col("f.properties.place").alias("place"),
        F.col("f.properties.tsunami").alias("tsunami"),
        F.col("f.properties.alert").alias("alert"),
        F.element_at("f.geometry.coordinates", 2).alias("depth_km"),
        F.element_at("f.geometry.coordinates", 1).alias("latitude"),
        F.element_at("f.geometry.coordinates", 0).alias("longitude"),
    ).withColumns({
        "event_time_utc": F.to_utc_timestamp(F.to_timestamp((F.col("time_ms")/1000).cast("timestamp")), "UTC"),
        "updated_utc":    F.to_utc_timestamp(F.to_timestamp((F.col("updated_ms")/1000).cast("timestamp")), "UTC"),
    }).drop("time_ms","updated_ms")

def write_silver(df, out_path):
    (df.write
       .mode("append")
       .format("parquet")
       .option("compression","snappy")
       .save(out_path))

def upsert_postgres(df, env):
    # For MVP we’ll do "last write wins" via write then SQL MERGE in a follow-up step.
    # Simpler: write to a temp table, then merge with a small JDBC query executed from Spark.
    jdbc_url = f"jdbc:postgresql://{env['PG_HOST']}:{env['PG_PORT']}/{env['PG_DB']}"
    props = {
        "user": env["PG_USER"],
        "password": env["PG_PASSWORD"],
        "driver": "org.postgresql.Driver"
    }
    # Write to staging table
    (df.write
       .mode("overwrite")
       .option("truncate","true")
       .jdbc(jdbc_url, f"{env['PG_schema_temp'] if 'PG_schema_temp' in env else env['PG_SCHEMA']}.eq_staging_latest", properties=props))
    # Use simple upsert by executing SQL after this job (Airflow task does it). Keeping transform pure.

def main():
    env = get_env()
    now = datetime.utcnow()

    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    # Read all JSON files dropped into bronze for the current hour
    bronze_hour_path = f"/opt/data/bronze/dt={now.strftime('%Y-%m-%d')}/HH={now.strftime('%H')}"
    df = spark.read.schema(schema_geojson()).json(bronze_hour_path)
    flat = flatten(df)

    # Partitioned silver write
    write_silver(flat, silver_path(now))

    # Cache a small "latest" subset for serving (e.g., last 24h) if needed later.
    # Upsert into Postgres is handled in a separate Airflow SQL task to keep concerns clean.

    spark.stop()

if __name__ == "__main__":
    main()

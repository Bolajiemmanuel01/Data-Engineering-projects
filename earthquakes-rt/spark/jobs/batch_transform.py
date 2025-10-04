# Batch transform: read bronze JSON snapshots, normalize, type-cast, write Parquet (silver),
# and write a staging table to Postgres (gold UPSERT happens in Airflow).
#
# Run with:
# spark-submit --master spark://spark-master:7077 /opt/spark-apps/jobs/batch_transform.py

from pyspark.sql import SparkSession, functions as F, types as T
from pyspark.sql.window import Window
from datetime import datetime
from common import get_env, silver_path

def build_spark():
    # Use UTC end-to-end for deterministic partitioning & timestamps
    return (
        SparkSession.builder
        .appName("earthquakes-batch-transform")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

def schema_geojson():
    # Minimal schema for USGS GeoJSON feed (only fields we use for MVP)
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
                T.StructField("time", T.LongType()),       # epoch ms
                T.StructField("updated", T.LongType()),    # epoch ms
                T.StructField("alert", T.StringType()),
                T.StructField("tsunami", T.IntegerType()),
                T.StructField("magType", T.StringType()),
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
    # Explode features -> one row per event and normalize fields
    fdf = df.select(F.explode("features").alias("f"))
    out = fdf.select(
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
        # Epoch ms -> TIMESTAMP (UTC). We avoid to_utc_timestamp because we already pin session TZ to UTC.
        "event_time_utc": F.to_timestamp((F.col("time_ms")/1000).cast("timestamp")),
        "updated_utc":    F.to_timestamp((F.col("updated_ms")/1000).cast("timestamp")),
    }).drop("time_ms","updated_ms")

    # Deduplicate by event_id, prefer the most recently updated record (handles USGS post-corrections)
    win = Window(F.col("event_time_utc"), "1 day")  # not used directly, but illustrating alternative
    # Simple dedup using updated_utc:
    out = (out
           .withColumn("rn", F.row_number().over(
               Window.partitionBy("event_id").orderBy(F.col("updated_utc").desc_nulls_last())
           ))
           .where("rn = 1")
           .drop("rn"))

    return out

def write_silver(df, out_path):
    # Append into partitioned Parquet (dt, HH derived from "now" at runtime by caller)
    (df.write
       .mode("append")
       .format("parquet")
       .option("compression","snappy")
       .save(out_path))

def write_staging_postgres(df, env):
    """
    Write current batch to Postgres staging table (eq_staging_latest).
    Airflow will MERGE/UPSERT staging into earthquakes_latest (gold).
    """
    cols = ["event_id","event_time_utc","magnitude","mag_type","latitude","longitude",
            "depth_km","place","tsunami","alert","updated_utc"]
    df_out = df.select(*cols)

    jdbc_url = f"jdbc:postgresql://{env['PG_HOST']}:{env['PG_PORT']}/{env['PG_DB']}"
    props = {
        "user": env["PG_USER"],
        "password": env["PG_PASSWORD"],
        "driver": "org.postgresql.Driver",
    }

    # Overwrite staging each run (idempotent; downstream UPSERT makes it safe)
    (df_out.write
        .mode("overwrite")
        .option("truncate", "true")
        .jdbc(jdbc_url, f"{env['PG_SCHEMA']}.eq_staging_latest", properties=props))

def main():
    env = get_env()
    now = datetime.utcnow()
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    # Candidate hour partitions to try (current hour, then previous hour)
    candidates = [
        f"/opt/data/bronze/dt={now:%Y-%m-%d}/HH={now:%H}",
        f"/opt/data/bronze/dt={(now):%Y-%m-%d}/HH={(now.hour-1)%24:02d}"
    ]

    import glob, os
    json_files = []
    real_base = None
    for base in candidates:
        files = glob.glob(os.path.join(base, "*.json"))
        if files:
            json_files = files
            real_base = base
            break

    if not json_files:
        # Nothing to process this run; exit gracefully
        spark.stop()
        return

    # Read only the files we found (avoids the “Spark saw a file that vanished” issue)
    df_raw = spark.read.schema(schema_geojson()).json(json_files)
    flat = flatten(df_raw)

    # Use the directory we actually read from to decide silver partition
    # If you prefer “current hour only”, keep silver_path(now)
    write_silver(flat, silver_path(now))

    # Stage to Postgres for UPSERT in Airflow
    write_staging_postgres(flat, env)

    spark.stop()


if __name__ == "__main__":
    main()

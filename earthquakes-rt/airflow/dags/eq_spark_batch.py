"""
Run Spark batch to convert bronze -> silver and stage to Postgres,
then UPSERT into gold table (earthquakes_latest).
"""
import os
import pendulum
from datetime import timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.python import PythonOperator
from docker.types import Mount  # <-- NEW: use Mount objects
import psycopg2

# --------- EDIT THIS to your absolute repo path on Windows ----------
# Example: r"C:\Users\a\OneDrive\Desktop\Data-Engineering-projects"
REPO = r"C:\Users\a\OneDrive\Desktop\Data-Engineering-projects"

SPARK_DIR = rf"{REPO}\earthquakes-rt\spark"
DATA_DIR  = rf"{REPO}\earthquakes-rt\data"
JARS_DIR  = rf"{REPO}\earthquakes-rt\spark\jars"
JDBC_JAR  = "/opt/spark-apps/jars/postgresql-42.7.3.jar"  # container path

# Postgres settings
PG_HOST = os.getenv("PG_HOST", "postgres")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB   = os.getenv("PG_DB", "earthquakes")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASS = os.getenv("PG_PASSWORD", "postgres")
PG_SCHEMA = os.getenv("PG_SCHEMA", "public")

UPSERT_SQL = f"""
INSERT INTO {PG_SCHEMA}.earthquakes_latest (
  event_id, event_time_utc, magnitude, mag_type, latitude, longitude, depth_km, place, tsunami, alert, updated_utc
)
SELECT event_id, event_time_utc, magnitude, mag_type, latitude, longitude, depth_km, place, tsunami, alert, updated_utc
FROM {PG_SCHEMA}.eq_staging_latest
ON CONFLICT (event_id) DO UPDATE SET
  event_time_utc = EXCLUDED.event_time_utc,
  magnitude      = EXCLUDED.magnitude,
  mag_type       = EXCLUDED.mag_type,
  latitude       = EXCLUDED.latitude,
  longitude      = EXCLUDED.longitude,
  depth_km       = EXCLUDED.depth_km,
  place          = EXCLUDED.place,
  tsunami        = EXCLUDED.tsunami,
  alert          = EXCLUDED.alert,
  updated_utc    = EXCLUDED.updated_utc;
"""

def run_upsert():
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(UPSERT_SQL)
    conn.close()

default_args = {
    "owner": "emmanuel",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="eq_spark_batch",
    start_date=pendulum.datetime(2025, 10, 4, tz="UTC"),
    schedule="@hourly",  # trigger manually for MVP; make "@hourly" later
    catchup=False,
    default_args=default_args,
    tags=["earthquakes", "silver", "gold"],
) as dag:

    spark_batch = DockerOperator(
        task_id="spark_bronze_to_silver_and_stage",
        image="apache/spark:3.5.1",
        api_version="auto",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode="data-engineering-projects_default",
        mount_tmp_dir=False,
        # network_mode optional; default works since we talk to spark-master by name (same Docker network)
        command=[
            "/opt/spark/bin/spark-submit",
            "--master", "spark://spark-master:7077",
            "--jars", JDBC_JAR,
            "/opt/spark-apps/jobs/batch_transform.py",
        ],
        # <-- CHANGED: use Mount objects instead of 'volumes'
        mounts=[
            Mount(target="/opt/spark-apps",     source=SPARK_DIR, type="bind", read_only=False),
            Mount(target="/opt/data",           source=DATA_DIR,  type="bind", read_only=False),
            Mount(target="/opt/spark-apps/jars",source=JARS_DIR,  type="bind", read_only=False),
        ],
        environment={
            "PG_HOST": PG_HOST,
            "PG_PORT": str(PG_PORT),
            "PG_DB": PG_DB,
            "PG_USER": PG_USER,
            "PG_PASSWORD": PG_PASS,
            "PG_SCHEMA": PG_SCHEMA,
            "DATA_ROOT": "/opt/data",
        },
    )

    upsert_gold = PythonOperator(
        task_id="gold_upsert",
        python_callable=run_upsert,
    )

    spark_batch >> upsert_gold

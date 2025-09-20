"""
Run Spark batch to convert bronze -> silver
Then (optionally) run SQL to upsert into Postgres (gold).
"""

import os, pendulum
from datetime import timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

DATA_ROOT = os.getenv("DATA_ROOT", "/opt/airflow/data")
SPARK_SUBMIT = os.getenv("SPARK_SUBMIT", "spark-submit")
PG_SCHEMA = os.getenv("PG_SCHEMA", "public")

default_args = {
    "owner": "emmanuel",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="eq_spark_batch",
    start_date=pendulum.datetime(2025, 9, 20, tz="UTC"),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["earthquakes", "silver", "gold"],
) as dag:
    # Option A: run spark-submit inside spark-master container via docker SDK
    spark_batch = DockerOperator(
        task_id="spark_bronze_to_silver",
        image="bitnami/spark:3.5",
        api_version="auto",
        auto_remove=True,
        command=[
            "spark-submit",
            "--master","spark://spark-master:7077",
            "/opt/spark-apps/jobs/batch_transform.py"
        ],
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        mounts=[
            # mount code and data into ephemeral container
            {"Source": "/absolute/path/to/your/repo/earthquakes-rt/spark", "Target": "/opt/spark-apps", "Type": "bind"},
            {"Source": "/absolute/path/to/your/repo/earthquakes-rt/data", "Target": "/opt/data", "Type": "bind"},
        ],
    )

    # Placeholder: after transform, we would upsert to Postgres by running SQL.
    upsert = PostgresOperator(
        task_id="gold_upsert_placeholder",
        postgres_conn_id="postgres_default",
        sql=f"SELECT 1;",  # we’ll replace with real MERGE once staging write is added
    )

    spark_batch >> upsert
# dags/nyc_taxi_ingest.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
import pandas as pd
from pathlib import Path

# Directory where all your Parquet files live
DATA_DIR = Path(__file__).parent.parent / "data"

# Dynamically find all .parquet files under DATA_DIR
# Sorted just for predictable load order
PARQUET_FILES = sorted(DATA_DIR.glob("*.parquet"))

# Connection ID and target staging table
CONN_ID = "nyc_taxi_db"
STAGING_TABLE = "staging.yellow_taxi_raw"

def ingest_to_postgres(**context):
    """
    Ingest each Parquet file into Postgres.
    - Ensures staging schema exists.
    - Truncates staging table once.
    - Loops over PARQUET_FILES so new files auto-load.
    """
    hook   = PostgresHook(postgres_conn_id=CONN_ID)
    engine = hook.get_sqlalchemy_engine()

    # 1) Ensure the staging schema exists
    hook.run("CREATE SCHEMA IF NOT EXISTS staging;")

    # 2) Truncate the staging table so reruns don't duplicate
    hook.run(f"DROP TABLE IF EXISTS {STAGING_TABLE};")

    # 3) Loop through every Parquet file we find
    for parquet_path in PARQUET_FILES:
        # 3a) Read the Parquet into a DataFrame
        df = pd.read_parquet(parquet_path)

        # 3b) Write to Postgres staging table
        df.to_sql(
            name=STAGING_TABLE.split(".")[1],   # 'yellow_taxi_raw'
            schema=STAGING_TABLE.split(".")[0], # 'staging'
            con=engine,
            if_exists="append",
            index=False,
            method="multi",       # send batches of rows per INSERT
            chunksize=10000       # tweak this for your memory / DB size
        )
        # Log how many rows we loaded per file
        context['ti'].log.info(
            f"Loaded {len(df):,} rows from {parquet_path.name}"
        )

# Define the DAG
with DAG(
    dag_id="nyc_taxi_pipeline",
    start_date=datetime(2025, 7, 30),
    schedule_interval="@daily",
    catchup=False,
    tags=["nyc_taxi"]
) as dag:

    ingest_task = PythonOperator(
        task_id="ingest_nyc_taxi",
        python_callable=ingest_to_postgres,
        provide_context=True,
    )

    ingest_task  # only task for now
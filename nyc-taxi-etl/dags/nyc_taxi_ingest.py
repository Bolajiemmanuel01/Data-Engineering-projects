# dags/nyc_taxi_ingest.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
import pandas as pd
from io import StringIO
from pathlib import Path
import pyarrow.dataset as ds

DATA_DIR     = Path(__file__).parent.parent / "data"
PARQUET_GLOB = "*.parquet"
PARQUET_FILES = sorted(DATA_DIR.glob(PARQUET_GLOB))

CONN_ID       = "nyc_taxi_db"               # must point at your nyc_taxi DB
STG_SCHEMA    = "staging"
STG_TABLE     = "yellow_taxi_raw"           # we’ll COPY into staging.yellow_taxi_raw

def ingest_to_postgres(**context):
    hook   = PostgresHook(postgres_conn_id=CONN_ID)
    engine = hook.get_sqlalchemy_engine()

    # 1) Ensure staging schema exists
    hook.run(f"CREATE SCHEMA IF NOT EXISTS {STG_SCHEMA};")

    # 2) Drop the old table if it exists (fast, avoids OOM)
    hook.run(f"DROP TABLE IF EXISTS {STG_SCHEMA}.{STG_TABLE};")

    # 3) Loop through every parquet file
    for path in PARQUET_FILES:
        # Read the parquet file
        dataset = ds.dataset(path, format="parquet")
        # Batch the dataset into manageable chunks
        for batch in dataset.to_batches(batch_size=50000):
            # Convert each batch to a pandas DataFrame
            df = batch.to_pandas()
            # Convert to CSV in-memory
            buf = StringIO()
            # Write the DataFrame to the buffer
            df.to_csv(buf, index=False)
            # Seek to the beginning of the buffer
            buf.seek(0)
            # COPY into Postgres (much faster than INSERTs)
            hook.copy_expert(
                sql=f"COPY {STG_SCHEMA}.{STG_TABLE} FROM STDIN WITH CSV HEADER",
                filename_or_file=buf
            )

        context['ti'].log.info(f"✅ Loaded {len(df):,} rows from {path.name}")

with DAG(
    dag_id="nyc_taxi_pipeline",
    start_date=datetime(2025, 7, 30),
    schedule_interval="@daily",
    catchup=False,
    tags=["nyc_taxi"],
) as dag:

    ingest = PythonOperator(
        task_id="ingest_nyc_taxi",
        python_callable=ingest_to_postgres,
        provide_context=True,
    )

    ingest
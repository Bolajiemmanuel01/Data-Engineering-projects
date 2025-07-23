from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
from pathlib import Path

# Constants, here are the CSV files we want to Ingest
CSV_FILES = [
    Path(__file__).parent.parent / "data" / "year_2009_2010.csv",
    Path(__file__).parent.parent / "data" / "year_2010_2011.csv",
]

STAGING_TABLE = "staging.online_retail_raw"
CONN_ID = "online_retail_db"

def ingest_to_postgres(**context):
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    engine = hook.get_sqlalchemy_engine()

    for csv_path in CSV_FILES:
        df = pd.read_csv(csv_path)
        df.to_sql(
            name=STAGING_TABLE.split(".")[1],
            name=STAGING_TABLE.split(".")[0],
            con=engine,
            if_exists="append",
            index=False
        )
        context['ti'].log.info(f"Loaded {len(df)} rows from {csv_path.name}")

with DAG

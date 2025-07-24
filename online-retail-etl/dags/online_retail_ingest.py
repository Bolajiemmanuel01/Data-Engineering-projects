from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
from pathlib import Path

# Constants, here are the CSV files we want to Ingest
# List of CSV file paths to ingest
# We build each Path relative to this script’s location
CSV_FILES = [
    Path(__file__).parent.parent / "data" / "year_2009_2010.csv",
    Path(__file__).parent.parent / "data" / "year_2010_2011.csv",
]

# Target staging table in the form "schema.table"
STAGING_TABLE = "staging.online_retail_raw"

# Airflow connection ID for PostgreSQL
CONN_ID = "online_retail_db"

def ingest_to_postgres(**context):
    """
    Read each CSV and append its contents into the staging table.
    """

    # Create a hook to connect to Postgres using the given connection ID
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    # Obtain a SQLAlchemy engine from the hook for pandas to_sql
    engine = hook.get_sqlalchemy_engine()

    # Loop through each CSV file path
    for csv_path in CSV_FILES:
        # Read CSV into a pandas DataFrame
        df = pd.read_csv(csv_path)
        # Write DataFrame to Postgres:
        # - name: table name without schema
        # - schema: schema part of STAGING_TABLE
        # - if_exists="append": add new rows to existing table
        # - index=False: don’t write DataFrame index as a column
        df.to_sql(
            name=STAGING_TABLE.split(".")[1],
            schema=STAGING_TABLE.split(".")[0],
            con=engine,
            if_exists="append",
            index=False
        )
        # Log how many rows were loaded from this file
        context['ti'].log.info(f"Loaded {len(df)} rows from {csv_path.name}")

# Define the DAG (Directed Acyclic Graph) for Airflow
with DAG(
    dag_id="online_retail_ingest",      # Unique Identifier
    start_date=datetime(2025, 7, 24),   # When to start scheduling
    schedule_interval="@daily",         # Run once Everyday
    catchup=False,                      # Don't backfill run's of past date
    tags=["online_retail"],             # UI Tagd for grouping
) as dag:
    
    # Task to run ingestion function
    ingest_task = PythonOperator(
        task_id="ingest_to_postgres",   # unique identifier for this task
        python_callable=ingest_to_postgres, # Function to perform
        provide_context=True,           # Pass airflow context to the function
    )

import pendulum, os, psycopg2
from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Postgres settings
PG_HOST = os.getenv("PG_HOST", "postgres")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB   = os.getenv("PG_DB", "earthquakes")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASS = os.getenv("PG_PASSWORD", "postgres")
PG_SCHEMA = os.getenv("PG_SCHEMA", "public")

ROLLUP_SQL = """
INSERT INTO public.earthquakes_daily_counts (event_date, count_events, max_mag)
SELECT
  (event_time_utc AT TIME ZONE 'UTC')::date AS event_date,
  COUNT(*) AS count_events,
  MAX(magnitude) AS max_mag
FROM public.earthquakes_latest
GROUP BY 1
ON CONFLICT (event_date) DO UPDATE
SET count_events = EXCLUDED.count_events,
    max_mag      = EXCLUDED.max_mag;
"""

def upsert_daily_counts():
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(ROLLUP_SQL)
    conn.close()

default_args = {
    "owner": "emmanuel",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="eq_daily_rollup",
    start_date=pendulum.datetime(2025, 10, 28, tz="UTC"),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["earthquakes", "daily", "postgres", "aggregate", "gold", "trend"],
) as dag:

    upsert_daily_counts = PythonOperator(
        task_id="upsert_daily_counts",
        python_callable=upsert_daily_counts,
    )

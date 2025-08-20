# crypto_price_pipeline.py
# Airflow DAG: Fetch crypto prices from CoinGecko and store JSON in Postgres (bronze),
# then run dbt to build silver/gold models.
#
# Notes:
# - Uses Postgres connection "crypto_db" (create it in Airflow UI or via env AIRFLOW_CONN_CRYPTO_DB).
# - Reads coins/currency from Airflow Variables (CRYPTO_COINS, VS_CURRENCY) or env (COINS, VS_CURRENCY).
# - Paths assume DAGs are mounted at /opt/airflow/dags.

from __future__ import annotations
import os
import json
import time
import datetime as dt
from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
import requests

# ---------- Config ----------
DAG_ID = "crypto_price_pipeline"
POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "crypto_db")
DEFAULT_COINS = "bitcoin,ethereum,solana,binancecoin"
DEFAULT_CURRENCY = "usd"
DBT_DIR = "/opt/airflow/dbt/crypto_prices" # adjusted the path

def get_param(name: str, default: str) -> str:
    # Prefer Airflow Variable; fallback to env; else default
    try:
        val = Variable.get(name)
        if val:
            return val
    except Exception:
        pass
    return os.getenv(name, default)

def fetch_and_store(**context):
    """Call CoinGecko simple/price and insert raw JSON into bronze.crypto_prices_raw."""
    coins = get_param("CRYPTO_COINS", DEFAULT_COINS)
    vs_currency = get_param("VS_CURRENCY", DEFAULT_CURRENCY)

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coins,
        "vs_currencies": vs_currency,
        "include_market_cap": "true",
        "include_24hr_vol": "true",
    }

    # Simple retry for transient errors / rate limit (HTTP 429)
    last_exc = None
    for attempt in range(5):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)  # backoff
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            last_exc = e
            time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"Failed to fetch CoinGecko after retries: {last_exc}")

    retrieved_at = dt.datetime.utcnow().isoformat()
    payload_json = json.dumps(data)

    # Insert into Postgres (JSONB)
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    insert_sql = """
        INSERT INTO bronze.crypto_prices_raw (retrieved_at, source, vs_currency, payload)
        VALUES (%s, %s, %s, %s::jsonb)
    """
    hook.run(insert_sql, parameters=[retrieved_at, "coingecko", vs_currency, payload_json])

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": dt.timedelta(minutes=2),
}

with DAG(
    dag_id=DAG_ID,
    start_date=dt.datetime(2025, 8, 1),
    schedule_interval="@hourly",
    catchup=False,
    default_args=default_args,
    tags=["crypto", "elt", "dbt", "postgres"],
) as dag:

    # Initialize schemas & tables
    init_db = PostgresOperator(
        task_id="init_db",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql="include/sql/init.sql",
    )

    fetch_prices = PythonOperator(
        task_id="fetch_prices",
        python_callable=fetch_and_store,
    )

    # Run dbt build (deps + seeds + run). Requires dbt installed in Airflow image.
    dbt_env = {
        # dbt connection comes from env vars (see profiles.yml)
        "DBT_HOST": os.getenv("DBT_HOST", os.getenv("POSTGRES_HOST", "postgres")),
        "DBT_USER": os.getenv("DBT_USER", os.getenv("POSTGRES_USER", "postgres")),
        "DBT_PASSWORD": os.getenv("DBT_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres")),
        "DBT_PORT": os.getenv("DBT_PORT", os.getenv("POSTGRES_PORT", 5432)),
        "DBT_DB": os.getenv("DBT_DB", os.getenv("POSTGRES_DB", "crypto")),
    }

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            "export PATH=$PATH:/home/airflow/.local/bin; "
            "cd {{ params.dbt_dir }} && "
            "dbt deps --profiles-dir . && "
            "dbt seed --profiles-dir . && "
            "dbt run --profiles-dir ."
        ),
        env=dbt_env,
        params={"dbt_dir": DBT_DIR},
    )


    # ---------- Optional DAG to test ----------
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "export PATH=$PATH:/home/airflow/.local/bin; "
            "cd {{ params.dbt_dir }} && "
            "dbt test --profiles-dir ."
        ),
        env=dbt_env,
        params={"dbt_dir": DBT_DIR},
    )

    init_db >> fetch_prices >> dbt_build >> dbt_test

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
# Minimal Great Expectations checks on Postgres data using a Pandas batch.
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowFailException
from great_expectations.dataset import PandasDataset  # simple dataset API
import textwrap
import pandas as pd

# ---------- Config ----------
DAG_ID = "crypto_price_pipeline"
POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "crypto_db")
DEFAULT_COINS = "bitcoin,ethereum,solana,binancecoin"
DEFAULT_CURRENCY = "usd"
DBT_DIR = "/opt/airflow/dbt/crypto_prices" # adjusted the path


def _resolve_table(hook: PostgresHook, candidates):
    """
    Return the first existing 'schema.table' from candidates list.
    Handles dbt's 'public_<custom_schema>' pattern.
    """
    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            for full in candidates:
                cur.execute("SELECT to_regclass(%s)", (full,))
                val = cur.fetchone()[0]
                if val:
                    return full
    return None


def run_quality_checks(conn_id: str = "crypto_db", max_age_hours: int = 24) -> None:
    """
    Great Expectations + lightweight SQL asserts:
      - bronze freshness (raw table updated recently)
      - staging presence/shape (price not null, >=0, vs_currency in 'usd')
      - expected coins present in recent data (from dbt seed 'coins')
      - uniqueness in points and daily tables
      - reasonable bounds on daily pct change
      - non-negative (mostly) for market_cap and volume_24h
    Raises AirflowFailException on any failure.
    """
    hook = PostgresHook(postgres_conn_id=conn_id)  # Create a Postgres hook

    # ---- 0) Resolve actual table names (dbt may use public_<schema>) ----
    bronze_raw = "bronze.crypto_prices_raw"
    stg_candidates   = ["silver.stg_crypto_prices", "public_silver.stg_crypto_prices"]
    daily_candidates = ["gold.fct_price_daily", "public_gold.fct_price_daily"]
    points_candidates= ["gold.fct_price_points", "public_gold.fct_price_points"]
    coins_candidates = ["silver.coins", "public_silver.coins"]

    stg_table    = _resolve_table(hook, stg_candidates) # Staging table
    daily_table  = _resolve_table(hook, daily_candidates) # Daily table
    points_table = _resolve_table(hook, points_candidates) # Points table
    coins_table  = _resolve_table(hook, coins_candidates) # Coins table

    # Validate resolved table names
    if not stg_table:
        raise AirflowFailException(f"Could not find staging table from candidates: {stg_candidates}")
    if not daily_table:
        raise AirflowFailException(f"Could not find daily table from candidates: {daily_candidates}")
    if not points_table:
        raise AirflowFailException(f"Could not find points table from candidates: {points_candidates}")
    if not coins_table:
        raise AirflowFailException(f"Could not find coins seed table from candidates: {coins_candidates}")

    # ---- 1) Bronze freshness: recent raw rows exist ----
    sql_max_raw = f"SELECT MAX(retrieved_at) FROM {bronze_raw};"
    max_raw = hook.get_first(sql_max_raw)[0]
    if max_raw is None:
        raise AirflowFailException("bronze.crypto_prices_raw is empty.")
    
    # Check within last N hours
    sql_fresh = f"SELECT NOW() - INTERVAL '{max_age_hours} hours' <= %s"
    is_fresh = hook.get_first(sql_fresh, parameters=(max_raw,))[0]
    if not is_fresh:
        raise AirflowFailException(
            f"Raw data stale: latest in bronze is {max_raw}, older than {max_age_hours}h."
        )

    # ---- 2) Load recent staging rows & coins for expectations ----
    stg_sql = f"""
        SELECT retrieved_at, coin_id, vs_currency, price, market_cap, volume_24h
        FROM {stg_table}
        WHERE retrieved_at >= NOW() - INTERVAL '{max_age_hours} hours'
        ORDER BY retrieved_at DESC
    """
    stg_df = hook.get_pandas_df(stg_sql)
    if stg_df.empty:
        raise AirflowFailException(
            f"No recent rows in {stg_table} within last {max_age_hours}h."
        )

    coins_df = hook.get_pandas_df(f"SELECT id FROM {coins_table}")
    expected_coins = set(coins_df["id"].dropna().astype(str).str.strip().tolist())

    # --- 2a) Ensure all expected coins appear in recent staging data ---
    seen_coins = set(stg_df["coin_id"].dropna().astype(str).str.strip().unique().tolist())
    missing = sorted(list(expected_coins - seen_coins))
    if missing:
        raise AirflowFailException(
            f"Missing expected coins in recent staging data: {missing}"
        )

    # ---- 3) Great Expectations on staging data (not nulls, ranges, currency) ----
    g_stg = PandasDataset(stg_df)
    results = []
    results.append(g_stg.expect_table_row_count_to_be_between(min_value=1))
    results.append(g_stg.expect_column_values_to_not_be_null("price"))
    results.append(g_stg.expect_column_values_to_be_between("price", min_value=0))
    results.append(g_stg.expect_column_values_to_not_be_null("coin_id"))
    results.append(g_stg.expect_column_values_to_be_in_set("vs_currency", ["usd"]))
    # allow most rows to have non-negative market_cap/volume (some APIs can return nulls)
    results.append(g_stg.expect_column_values_to_be_between("market_cap", min_value=0, mostly=0.95))
    results.append(g_stg.expect_column_values_to_be_between("volume_24h", min_value=0, mostly=0.95))

    # ---- 4) Points uniqueness & Daily sanity checks ----
    points_df = hook.get_pandas_df(f"SELECT retrieved_at, coin_id, vs_currency, price FROM {points_table}")
    if points_df.empty:
        raise AirflowFailException(f"{points_table} is empty after dbt run.")
    g_pts = PandasDataset(points_df)
    results.append(g_pts.expect_compound_columns_to_be_unique(["retrieved_at", "coin_id", "vs_currency"]))
    results.append(g_pts.expect_column_values_to_be_between("price", min_value=0))

    daily_df = hook.get_pandas_df(f"""
        SELECT day, coin_id, vs_currency, avg_price, pct_change_vs_prev_day
        FROM {daily_table}
    """)
    if daily_df.empty:
        raise AirflowFailException(f"{daily_table} is empty after dbt run.")
    g_daily = PandasDataset(daily_df)
    results.append(g_daily.expect_compound_columns_to_be_unique(["day", "coin_id", "vs_currency"]))
    results.append(g_daily.expect_column_values_to_not_be_null("avg_price"))
    # pct change should be a reasonable number, but still allow huge swings; cap at ±1000%
    results.append(g_daily.expect_column_values_to_be_between("pct_change_vs_prev_day", min_value=-1000, max_value=1000, mostly=0.99))

    # ---- 5) Aggregate failures ----
    failed = [r for r in results if not r.get("success", False)]
    if failed:
        bad = [r["expectation_config"]["expectation_type"] for r in failed]
        raise AirflowFailException(f"Great Expectations failed: {bad}")


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


    gx_checks = PythonOperator(
        task_id="gx_checks",
        python_callable=run_quality_checks,
        op_kwargs={"conn_id": POSTGRES_CONN_ID, "max_age_hours": 24},
    )

    init_db >> fetch_prices >> dbt_build >> dbt_test >> gx_checks

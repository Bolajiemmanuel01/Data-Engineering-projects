# include/quality_checks.py
# Minimal Great Expectations checks on Postgres data using a Pandas batch.

from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowFailException
from great_expectations.dataset import PandasDataset  # simple dataset API
import textwrap

def run_quality_checks(conn_id: str = "crypto_db", max_age_hours: int = 24) -> None:
    """
    Pull recent rows from silver.stg_crypto_prices and assert:
      - table has at least 1 row
      - price is not null
      - price is >= 0
      - coin_id is not null and exists
      - vs_currency is 'usd'
    Raises AirflowFailException if any expectation fails.
    """

    hook = PostgresHook(postgres_conn_id=conn_id)  # Create a Postgres hook

    sql = textwrap.dedent(f"""
        SELECT retrieved_at, coin_id, vs_currency, price, market_cap, volume_24h
        FROM silver.stg_crypto_prices
        WHERE retrieved_at >= NOW() - INTERVAL '{max_age_hours} hours'
        ORDER BY retrieved_at DESC
    """)
    df = hook.get_pandas_df(sql)

    if df.empty:
        raise AirflowFailException(
            f"No rows in silver.stg_crypto_prices in the last {max_age_hours} hours."
        )

    gdf = PandasDataset(df)

    results = []
    results.append(gdf.expect_table_row_count_to_be_between(min_value=1)) # at least 1 row
    results.append(gdf.expect_column_values_to_not_be_null("price")) # price is not null
    results.append(gdf.expect_column_values_to_be_between("price", min_value=0)) # price is >= 0
    results.append(gdf.expect_column_values_to_not_be_null("coin_id")) # coin_id is not null
    results.append(gdf.expect_column_values_to_be_in_set("vs_currency", ["usd"])) # vs_currency is 'usd'

    failed = [r for r in results if not r.get("success", False)]

    if failed:
        # Log failed expectations
        bad = [r["expectation_config"]["expectation_type"] for r in failed]
        raise AirflowFailException(f"Great Expectations failed: {bad}")

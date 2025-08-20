# Crypto Price Pipeline — Airflow + dbt + Postgres (Starter Kit)

This starter packs a minimal, production-style ELT:
- **Airflow DAG**: fetch crypto prices from CoinGecko and store raw JSON in Postgres (**bronze**).
- **dbt project**: transform JSON to typed tables (**silver**) and daily aggregates (**gold**).
- **Postgres**: schemas `bronze`, `silver`, `gold` with a single raw table to start.

> You already have Docker with Airflow + Postgres. Drop these folders into your repo and mount the `airflow/dags` and `dbt` folders inside the Airflow container (typical path: `/opt/airflow/dags`).

---

## Quickstart

1) **Create/confirm a Postgres database** (e.g., `crypto`). If needed:
```sql
-- run in your Postgres (psql/pgAdmin etc.)
CREATE DATABASE crypto;
```

2) **Airflow Connection** (recommended)
Create a connection in Airflow UI **(Admin → Connections)**:
- Conn Id: `crypto_db`
- Conn Type: `Postgres`
- Host: your Postgres service name (often `postgres` inside Docker)
- Schema (DB): `crypto`
- Login: `airflow` (or your username)
- Password: `airflow` (or your password)
- Port: `5432`

Alternatively, set environment variable in Airflow:  
`AIRFLOW_CONN_CRYPTO_DB=postgresql+psycopg2://<user>:<pwd>@<host>:5432/<db>`

3) **Install Python deps in the Airflow image** (from inside the webserver/scheduler container):
```bash
pip install -r /opt/airflow/dags/requirements.txt
```
This installs `requests`, `psycopg2-binary`, `apache-airflow-providers-postgres`, `dbt-core`, `dbt-postgres`.

4) **dbt env vars** (make these available to the Airflow container; edit `.env.example` and wire into Docker):
```
DBT_HOST=postgres
DBT_USER=airflow
DBT_PASSWORD=airflow
DBT_PORT=5432
DBT_DB=crypto
```

5) **Coins + currency**  
Edit Airflow **Variables** or `.env` (both supported by DAG):
- Variable `CRYPTO_COINS` e.g. `bitcoin,ethereum,solana,binancecoin`
- Variable `VS_CURRENCY` e.g. `usd`

6) **Start the DAG**  
- Place `airflow/dags/*` under your Airflow DAGs path.
- In the Airflow UI, turn on the DAG **`crypto_price_pipeline`**.
- The first task `init_db` creates schemas/tables.
- `fetch_prices` calls CoinGecko and inserts JSON rows.
- `dbt_build` runs the dbt project to create silver/gold tables.

---

## Repository layout (suggested)

```
.
├─ airflow/
│  ├─ dags/
│  │  ├─ crypto_price_pipeline.py
│  │  └─ include/sql/init.sql
│  └─ requirements.txt
├─ dbt/
│  └─ crypto_prices/
│     ├─ dbt_project.yml
│     ├─ profiles.yml
│     ├─ models/
│     │  ├─ sources.yml
│     │  ├─ staging/stg_crypto_prices.sql
│     │  └─ marts/
│     │     ├─ fct_price_points.sql
│     │     └─ fct_price_daily.sql
│     └─ seeds/coins.csv
├─ .env.example
└─ .gitignore
```

---

## Notes & Scaling

- Add more fields from CoinGecko by tweaking the DAG request.
- Switch schedule from hourly to every 15–30 minutes if needed.
- Convert `fct_price_points` to **incremental** (already configured) for scale.
- Add dbt tests (`unique`, `not_null`) and docs later.
- Optional: expose a Power BI/Metabase/Grafana dashboard from the **gold** tables.

**Enjoy!** – This is intentionally minimal but extensible.

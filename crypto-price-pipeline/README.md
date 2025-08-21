# Crypto Price Pipeline — Airflow + dbt + Postgres
[![dbt CI](https://github.com/Bolajiemmanuel01/Data-Engineering-projects/actions/workflows/dbt-ci.yml/badge.svg)](https://github.com/Bolajiemmanuel01/Data-Engineering-projects/actions/workflows/dbt-ci.yml)
[![Publish dbt docs](https://github.com/Bolajiemmanuel01/Data-Engineering-projects/actions/workflows/publish-docs.yml/badge.svg)](https://github.com/Bolajajoemmanuel01/Data-Engineering-projects/actions/workflows/publish-docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Airflow](https://img.shields.io/badge/Airflow-2.x-blue)
![dbt](https://img.shields.io/badge/dbt-1.7.x-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)
![Built with Docker](https://img.shields.io/badge/Built%20with-Docker-2496ED)

End‑to‑end ELT pipeline that ingests **CoinGecko** crypto prices, stores raw JSON in **Postgres** (bronze), transforms with **dbt** (silver/gold), orchestrated by **Airflow**, and validated with **Great Expectations**.

## Quickstart
1. **Create DB** (once):
   ```bash
   docker compose exec postgres psql -U postgres -c "CREATE DATABASE crypto;"
   ```
2. **Create Airflow connection** (once):
   ```bash
   docker compose exec airflow airflow connections add crypto_db      --conn-type postgres --conn-login postgres --conn-password postgres      --conn-host postgres --conn-port 5432 --conn-schema crypto
   ```
3. **Coins & currency** (env or Airflow Variables):
   - `CRYPTO_COINS=bitcoin,ethereum,solana,binancecoin`
   - `VS_CURRENCY=usd`
4. Enable the DAG **`crypto_price_pipeline`** in Airflow → Trigger a run.
5. Verify:
   ```bash
   docker compose exec postgres psql -U postgres -d crypto -c "SELECT COUNT(*) FROM gold.fct_price_daily;"
   ```

## Data model
- **bronze.crypto_prices_raw** — raw JSON (payload)
- **silver.stg_crypto_prices** — flattened, typed
- **gold.fct_price_points** — incremental points
- **gold.fct_price_daily** — daily aggregates (+ pct change)
- **gold.vw_crypto_daily** — friendly view for dashboards (see `db/sql/views.sql`)

## DAG
`init_db → fetch_prices → dbt_build → gx_checks` (schedule: `@hourly` by default)

## Quality
- **dbt tests**: not_null / accepted_values / relationships
- **GX**: bronze freshness, expected coins present, not-null/≥0, uniqueness on facts, % change sanity

## Power BI
Connect to PostgreSQL:
- Server: `localhost`  Port: `5433`
- Database: `crypto`  User/Pass: `postgres/postgres`
Load `gold.vw_crypto_daily`. Sample measures are in the DOCX included.

## Grafana (optional)
Add this service to `docker-compose.yaml`:
```yaml
grafana:
  image: grafana/grafana:10.4.3
  ports: ["3000:3000"]
  volumes:
    - ./crypto-price-pipeline/grafana/provisioning:/etc/grafana/provisioning
  environment:
    - GF_SECURITY_ADMIN_USER=admin
    - GF_SECURITY_ADMIN_PASSWORD=admin
  depends_on:
    - postgres
```
Datasource provisioning file: `grafana/provisioning/datasources/postgres.yaml`.

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
├─ .gitignore
├─grafana/provisioning/datasources/postgres.yaml
├─db/sql/views.sql
├─README.md
└─LICENSE
```

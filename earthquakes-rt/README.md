# Real-Time Earthquake Data Pipeline (Spark + Airflow + Postgres + Grafana)

## Overview
This project ingests live global earthquake data from the USGS public API and turns it into analytics and dashboards.

**Goal**: Ingest USGS earthquake data, land raw (bronze), clean/enrich (silver) with Spark, and serve curated (gold) to Postgres for dashboards.  
**Phases**: Batch MVP → Kafka + Spark Streaming → Data Quality → Alerts.

---

**Key features:**
- Ingestion of near real-time earthquake events (USGS GeoJSON feed).
- Bronze / Silver / Gold medallion architecture.
- Distributed processing using Apache Spark.
- Hourly batch orchestration using Apache Airflow.
- Serving layer in Postgres for BI / dashboards.
- Grafana dashboard of recent earthquakes and trends.

This is designed to look and behave like a production data platform.

## Medallion Layout
- **Bronze**: Raw GeoJSON snapshots from USGS
- **Silver**: Cleaned/typed Parquet (partitioned by date/hour)
- **Gold**: Curated table(s) in Postgres for BI

## Local Paths
- `data/bronze`, `data/silver`, `data/gold` – bind-mounted into containers

---

```
earthquakes-rt/
├─ README.md
├─ .env.example
├─ docker/
│  └─ compose.override.yml
├─ airflow/
│  └─ dags/
│     ├─ eq_poll_usgs.py
│     └─ eq_spark_batch.py
├─ spark/
│  ├─ jobs/
│  │  ├─ batch_transform.py
│  │  └─ common.py
│  └─ requirements.txt
├─ db/
│  ├─ init/
│  │  └─ 001_init_earthquakes.sql
│  └─ sql/
│     └─ upsert_gold.sql
├─ data/
│  ├─ bronze/        # raw json snapshots (time-partitioned)
│  ├─ silver/        # cleaned parquet (time-partitioned)
│  └─ gold/          # curated parquet or postgres
└─ grafana/
   └─ dashboards/
      └─ earthquakes_overview.json
```

---

## Architecture

### 1. Bronze layer (raw landing)
- Airflow task `eq_poll_usgs` calls the USGS API and writes each response to disk as timestamped JSON.
- Files are partitioned by date/hour:
  `data/bronze/dt=YYYY-MM-DD/HH=HH/usgs_*.json`

### 2. Silver layer (cleaned Parquet)
- Spark job (`batch_transform.py`) reads the bronze JSON.
- It explodes the GeoJSON `features[]` array, extracts:
  - `event_id`
  - `event_time_utc`, `updated_utc`
  - `magnitude`, `mag_type`
  - `latitude`, `longitude`, `depth_km`
  - `place`, `tsunami`, `alert`
- It deduplicates by `event_id`, keeping the latest revision from USGS.
- It writes columnar Parquet to:
  `data/silver/dt=YYYY-MM-DD/HH=HH/*.parquet`

### 3. Gold layer (serving tables in Postgres)
The Spark job also writes the most recent batch into a Postgres staging table:
- `public.eq_staging_latest`

Then an Airflow task runs an UPSERT into:
- `public.earthquakes_latest` → one row per earthquake id (latest known state)
- This table powers dashboards and queries.

A daily rollup DAG aggregates into:
- `public.earthquakes_daily_counts` → (event_date, count_events, max_mag)

### 4. Orchestration
- `eq_spark_batch` (Airflow DAG)
  - Runs hourly.
  - Step 1: Submits Spark to the Spark cluster (`spark-master` / `spark-worker` running in Docker).
  - Step 2: After Spark writes staging rows, runs SQL to merge those rows into `earthquakes_latest`.

- `eq_daily_rollup` (Airflow DAG)
  - Runs daily.
  - Maintains `earthquakes_daily_counts` for trend analysis.

### 5. Dashboard (Grafana)
Grafana is connected directly to Postgres.
Example visualizations:
- **Stat:** Earthquakes in the last 24 hours.
- **Time series:** Quakes per hour in the last 24 hours (`COUNT(*) GROUP BY date_trunc('hour', event_time_utc)`).
- **Table:** Significant quakes (magnitude ≥ 4.5) with location.
- **Trend:** Daily quake volume and max magnitude per day.
- (Optional) World map panel plotting latitude/longitude and coloring by magnitude.

---

## Tech Stack
- **Airflow**: scheduling & orchestration of ingestion and Spark.
- **Spark**: distributed batch / near-real-time style processing, bronze → silver + Postgres staging.
- **PostgreSQL**: serving layer for analytics & Grafana.
- **Grafana**: dashboard and monitoring layer.
- **Docker Compose**: runs Airflow, Spark master/worker, Postgres, Grafana together.
- **Python**: API ingestion, Spark job logic, Airflow DAGs.

---

## Why this project matters
This repo demonstrates:
- How to design and operate a medallion data lake (bronze/silver/gold).
- How to process streaming-like feeds with Spark in micro-batch style.
- How to land data in a warehouse-like store (Postgres) and expose it to BI.
- How to automate the entire flow with Airflow.
- How to build operations-facing dashboards (Grafana) over that data.

This is similar to what modern data engineering teams do for observability (pipeline health), telemetry (IoT/sensor streams), or public data monitoring.
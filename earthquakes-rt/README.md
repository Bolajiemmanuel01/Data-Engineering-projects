# Real-Time Earthquake Data Pipeline (Spark + Airflow + Postgres + Grafana)

**Goal**: Ingest USGS earthquake data, land raw (bronze), clean/enrich (silver) with Spark, and serve curated (gold) to Postgres for dashboards.  
**Phases**: Batch MVP → Kafka + Spark Streaming → Data Quality → Alerts.

## Components
- **Airflow**: Orchestrates polling + Spark jobs
- **Spark**: Batch transform now; streaming later
- **Postgres**: Serving layer (recent quakes + aggregates)
- **Grafana**: Live charts from Postgres

## Medallion Layout
- **Bronze**: Raw GeoJSON snapshots from USGS
- **Silver**: Cleaned/typed Parquet (partitioned by date/hour)
- **Gold**: Curated table(s) in Postgres for BI

## Local Paths
- `data/bronze`, `data/silver`, `data/gold` – bind-mounted into containers

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
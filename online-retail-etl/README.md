# Online Retail ETL & Analytics Pipeline

This folder contains an end-to-end **batch ETL pipeline** for the UCI Online Retail II dataset, built with **Apache Airflow** (ingestion) and **dbt** (data transformations), including automated testing and documentation.

---

## Table of Contents

1. [Project Overview](#project-overview)  
2. [Architecture](#architecture)  
3. [Folder Structure](#folder-structure)  
4. [Prerequisites](#prerequisites)  
5. [Local Setup](#local-setup)  
   - [1. Clone & Virtual Environment](#1-clone--virtual-environment)  
   - [2. Convert Excel to CSV](#2-convert-excel-to-csv)  
   - [3. Stand Up Airflow & Postgres](#3-stand-up-airflow--postgres)  
   - [4. Create Analytics Database & Schema](#4-create-analytics-database--schema)  
   - [5. Run the Ingestion DAG](#5-run-the-ingestion-dag)  
6. [dbt Project](#dbt-project)  
   - [1. Install dbt](#1-install-dbt)  
   - [2. Configure profiles.yml](#2-configure-profilesyml)  
   - [3. Run & Test Models](#3-run--test-models)  
   - [4. Generate & Serve Documentation](#4-generate--serve-documentation)  
7. [CI/CD & Documentation Deployment](#cicd--documentation-deployment)  
8. [Troubleshooting](#troubleshooting)  

---

## Project Overview

- **Dataset**: UCI Online Retail II (Dec 2009 – Dec 2011), UK-based online gift retailer.  
- **Goal**:  
  1. **Ingest** raw Excel data into Postgres daily via Airflow.  
  2. **Transform** and **test** data with dbt, building a Kimball-style star schema (staging → dims → fact).  
  3. **Automate** runs and tests with Airflow, and validate changes via GitHub Actions.  
  4. **Document** lineage & schema with dbt docs, deployed to GitHub Pages.

---

## Architecture

```
┌────────────────┐    ┌──────────────┐    ┌────────────────┐
│ OnlineRetail   │    │ Airflow      │    │ Postgres       │
│ Excel Workbook │─┐  │ DAG:         │    │ (airflow DB)   │
│                │ │  │ - convert    │─▶  │  - staging raw │
└────────────────┘ │  │   Excel→CSV  │    │  - airflow meta│
                   │  │ - ingest CSV │
                   │  │   → staging  │
                   │  └──────────────┘
                   │         │
                   │         ▼
                   │  ┌───────────────┐        ┌──────────┐
                   │  │ dbt           │─▶─────▶│ Postgres │
                   │  │ Models:       │ Build  │ (online_ │
                   │  │ - staging     │ Tables │ retail   │
                   │  │ - dims/fact   │ & Tests│ schema)  │
                   │  └───────────────┘        └──────────┘
                   │
                   └─ CI/CD via GitHub Actions
                       • dbt parse, run, test
                       • dbt docs generate & deploy
```

---

## Folder Structure

```
online-retail-etl/
├── data/
│   └── OnlineRetail.xlsx         # Raw Excel workbook
├── scripts/
│   └── convert_excel.py          # Converts Excel sheets → CSV
├── dags/
│   └── online_retail_ingest.py   # Airflow DAG for ingestion & dbt
├── online_retail_dbt/            # dbt project
│   ├── dbt_project.yml
│   └── models/
│       ├── schema.yml            # Sources, staging & mart tests
│       ├── stg_online_retail.sql
│       └── marts/
│           ├── dim_customer.sql
│           ├── dim_product.sql
│           ├── dim_date.sql
│           └── fct_sales.sql
├── docker-compose.yaml           # Airflow + Postgres services
└── README.md                     
```

---

## Prerequisites

- **Docker Desktop** (with Linux containers)  
- **Docker Compose v2**  
- **Python 3.9–3.12** on host  
- **pip**, **virtualenv** or **venv** support  
- (Optional) Local **psql** client for verification  

---

## Local Setup

### 1. Clone & Virtual Environment

```bash
git clone https://github.com/your-org/Data-Engineering-projects.git
cd Data-Engineering-projects/online-retail-etl

# Create & activate venv
python -m venv venv
# Windows
.
env\Scriptsctivate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

### 2. Convert Excel to CSV

```bash
cd scripts
python convert_excel.py
```

- Generates:
  ```
  ../data/online_retail_2009_2010.csv
  ../data/online_retail_2010_2011.csv
  ```

---

### 3. Stand Up Airflow & Postgres

```bash
cd ../            # back to online-retail-etl root
docker-compose up -d --build
```

- **Airflow UI**: http://localhost:8080 (admin/admin)
- **Postgres (airflow metadata)**: container `postgres`, port 5432

---

### 4. Create Analytics Database & Schema

```bash
# inside Postgres container
docker-compose exec postgres psql -U postgres -d airflow   -c "CREATE DATABASE online_retail;"
docker-compose exec postgres psql -U postgres -d online_retail   -c "CREATE SCHEMA IF NOT EXISTS staging;"
```

---

### 5. Run the Ingestion DAG

1. In Airflow UI, go to **DAGs** → **online_retail_pipeline**  
2. **Enable** and **Trigger** the DAG  
3. Verify in Postgres:
   ```sql
   -- connect inside container
   docker-compose exec postgres psql -U postgres -d online_retail

   -- check raw staging
   \dt staging.*
   SELECT COUNT(*) FROM staging.online_retail_raw;
   ```

---

## dbt Project

### 1. Install dbt

```bash
# Ensure venv is active
pip install dbt-core dbt-postgres
```

### 2. Configure profiles.yml

Edit `~/.dbt/profiles.yml`:

```yaml
online_retail_dbt:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5433          # if you remapped Postgres to 5433, else 5432
      user: postgres
      password: <your_password>
      dbname: online_retail
      schema: staging
      threads: 1
```

### 3. Run & Test Models

```bash
# from repo root
cd online_retail_dbt

dbt debug            # verify connection
dbt run              # build staging, dims, fact
dbt test             # run schema tests
```

### 4. Generate & Serve Documentation

```bash
dbt docs generate    # builds rich docs site in target/docs/
dbt docs serve       # view at http://localhost:8000
```

---

## CI/CD & Documentation Deployment

- **GitHub Actions** workflows live in `.github/workflows/` at repo root.  
  - **dbt-ci.yml**: runs `dbt parse`, `dbt run`, `dbt test` on PRs/push to `main`.  
  - **dbt-docs-deploy.yml**: generates docs and pushes to `gh-pages` branch.  

---

## Troubleshooting

- **Airflow container not starting**: ensure Docker Desktop is in Linux containers mode.  
- **dbt “relation does not exist”**: confirm `profiles.yml` points to the Docker Postgres (right host/port), and `quoting.database:false` is set in `dbt_project.yml`.  
- **Duplicate rows in staging**: check that the DAG’s `ingest_to_postgres` function truncates the table before load.


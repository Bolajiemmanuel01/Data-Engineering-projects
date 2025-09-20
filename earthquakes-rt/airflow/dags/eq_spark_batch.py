"""
Poll USGS feed every N minutes, save raw GeoJSON into bronze as a timestamped snapshot.
- Keeps raw copies (immutable) for reproducibility.
- Each run writes to: data/bronze/dt=YYYY-MM-DD/HH=HH/part-<ts>.json
"""

import os, json, requests, pathlib, pendulum
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator


USGS_FEED = os.getenv("USGS_FEED", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson")
POLL_INTERVAL_MIN = int(os.getenv("POLL_INTERVAL_MIN", "5"))
DATA_ROOT = os.getenv("DATA_ROOT", "/opt/airflow/data")  # bind this to ../data in docker
LOCAL_TZ = pendulum.timezone("UTC")


def fetch_and_land():
    now = datetime.utcnow()
    ymd = now.strftime("%Y-%m-%d")
    hh  = now.strftime("%H")
    out_dir = pathlib.Path(DATA_ROOT) / "bronze" / f"dt={ymd}" / f"HH={hh}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"usgs_{ts}.json"

    resp = requests.get(USGS_FEED, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    # (Optional) light touch: drop massive subfields if any; we keep full for MVP
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)

default_args = {
    "owner": "emmanuel",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="eq_poll_usgs",
    start_date=pendulum.datetime(2025, 9, 20, tz="UTC"),
    schedule=f"*/{POLL_INTERVAL_MIN} * * * *", # CRON Job
    catchup=False,
    default_args=default_args,
    tags=["earthquakes","bronze","usgs"],
) as dag:

    poll = PythonOperator(
        task_id="poll_usgs_and_land_bronze",
        python_callable=fetch_and_land,
    )

    poll
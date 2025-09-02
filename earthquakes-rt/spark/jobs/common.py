# Common utilities shared by batch & streaming jobs
import os
from datetime import datetime
from typing import Dict

def get_env() -> Dict[str, str]:
    return {
        "PG_HOST": os.getenv("PG_HOST", "postgres"),
        "PG_PORT": os.getenv("PG_PORT", "5432"),
        "PG_DB": os.getenv("PG_DB", "earthquakes"),
        "PG_USER": os.getenv("PG_USER", "postgres"),
        "PG_PASSWORD": os.getenv("PG_PASSWORD", "postgres"),
        "PG_SCHEMA": os.getenv("PG_SCHEMA", "public"),
        "DATA_ROOT": os.getenv("DATA_ROOT", "/opt/data"),
        "TZ": "UTC",
    }

def bronze_path(now: datetime) -> str:
    # partitioned raw snapshot path: /opt/data/bronze/dt=YYYY-MM-DD/HH=HH/
    return f"/opt/data/bronze/dt={now.strftime('%Y-%m-%d')}/HH={now.strftime('%H')}"

def silver_path(now: datetime) -> str:
    # cleaned parquet by same partitioning
    return f"/opt/data/silver/dt={now.strftime('%Y-%m-%d')}/HH={now.strftime('%H')}"

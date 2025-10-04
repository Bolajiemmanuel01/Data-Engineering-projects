# Common utilities shared by batch & streaming jobs
import os
from datetime import datetime
from typing import Dict

def get_env() -> Dict[str, str]:
    """
    Read environment variables (with safe defaults) for Spark jobs.
    """
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
    """
    Partitioned raw snapshot path:
    /opt/data/bronze/dt=YYYY-MM-DD/HH=HH
    """
    return f"/opt/data/bronze/dt={now:%Y-%m-%d}/HH={now:%H}"

def silver_path(now: datetime) -> str:
    """
    Partitioned cleaned parquet path:
    /opt/data/silver/dt=YYYY-MM-DD/HH=HH
    """
    return f"/opt/data/silver/dt={now:%Y-%m-%d}/HH={now:%H}"

# ---- Optional JDBC helpers (used by write_staging_postgres, and ready for future jobs) ----

def pg_jdbc_url(env: Dict[str, str]) -> str:
    """
    Build a JDBC URL for PostgreSQL from env.
    """
    return f"jdbc:postgresql://{env['PG_HOST']}:{env['PG_PORT']}/{env['PG_DB']}"

def pg_jdbc_props(env: Dict[str, str]) -> Dict[str, str]:
    """
    Spark JDBC properties dict for PostgreSQL.
    """
    return {
        "user": env["PG_USER"],
        "password": env["PG_PASSWORD"],
        "driver": "org.postgresql.Driver",
    }

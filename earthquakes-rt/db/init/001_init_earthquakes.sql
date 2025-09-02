-- Minimal serving table for gold layer (MVP)
CREATE TABLE IF NOT EXISTS public.earthquakes_latest (
    event_id        TEXT PRIMARY KEY,
    event_time_utc  TIMESTAMP NOT NULL,
    magnitude       NUMERIC,
    mag_type        TEXT,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    depth_km        DOUBLE PRECISION,
    place           TEXT,
    tsunami         INT,
    alert           TEXT,
    updated_utc     TIMESTAMP
);

-- Optional aggregate (we’ll fill later)
CREATE TABLE IF NOT EXISTS public.earthquakes_daily_counts (
    event_date      DATE PRIMARY KEY,
    count_events    INT,
    max_mag         NUMERIC
);
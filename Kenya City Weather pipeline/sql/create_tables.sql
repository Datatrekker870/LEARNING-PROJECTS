-- ======================================================================
-- KENYA CITY WEATHER PIPELINE — SCHEMA + UPSERTS
-- ======================================================================

-- ---------- 1. DIMENSIONS ----------

CREATE TABLE IF NOT EXISTS dim_city (
    city_id    INTEGER PRIMARY KEY,          -- Open-Meteo geocoding id
    name       VARCHAR(100) NOT NULL,
    county     VARCHAR(100),
    latitude   DOUBLE PRECISION NOT NULL,
    longitude  DOUBLE PRECISION NOT NULL,
    elevation  DOUBLE PRECISION,
    population BIGINT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date        DATE PRIMARY KEY,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    month_name  VARCHAR(20) NOT NULL,
    day_of_week INTEGER NOT NULL,            -- 1 = Monday ... 7 = Sunday
    is_weekend  BOOLEAN NOT NULL,
    season      VARCHAR(20) NOT NULL         -- Long rains / Short rains / Dry season
);

-- ---------- 2. FACT (FKs to both dimensions, composite PK) ----------

CREATE TABLE IF NOT EXISTS fact_daily_weather (
    city_id       INTEGER NOT NULL REFERENCES dim_city(city_id),
    weather_date  DATE    NOT NULL REFERENCES dim_date(date),
    temp_max      DOUBLE PRECISION,
    temp_min      DOUBLE PRECISION,
    temp_avg      DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    rain          DOUBLE PRECISION,
    wind_max      DOUBLE PRECISION,
    is_rainy_day  BOOLEAN NOT NULL,
    PRIMARY KEY (city_id, weather_date)
);

-- ---------- 3. CONTROL + QUALITY + MONITORING ----------

CREATE TABLE IF NOT EXISTS etl_watermark (
    city_id          INTEGER PRIMARY KEY REFERENCES dim_city(city_id),
    last_date_loaded DATE NOT NULL,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS rejected_records (
    id               SERIAL PRIMARY KEY,
    town_name        VARCHAR(100),
    observation_date DATE,
    reject_reason    TEXT NOT NULL,
    run_time         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS etl_run_log (
    run_id         SERIAL PRIMARY KEY,
    start_time     TIMESTAMPTZ NOT NULL,
    end_time       TIMESTAMPTZ,
    rows_extracted INTEGER NOT NULL DEFAULT 0,
    rows_loaded    INTEGER NOT NULL DEFAULT 0,
    rows_rejected  INTEGER NOT NULL DEFAULT 0,
    status         VARCHAR(20) NOT NULL,
    error_message  TEXT
);

-- ======================================================================
-- UPSERTS (referenced by load.py)
-- ======================================================================

-- name: upsert_city
INSERT INTO dim_city (city_id, name, county, latitude, longitude, elevation, population)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (city_id) DO UPDATE SET
    name       = EXCLUDED.name,
    county     = EXCLUDED.county,
    latitude   = EXCLUDED.latitude,
    longitude  = EXCLUDED.longitude,
    elevation  = EXCLUDED.elevation,
    population = EXCLUDED.population;

-- name: upsert_date
INSERT INTO dim_date (date, year, month, month_name, day_of_week, is_weekend, season)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (date) DO UPDATE SET
    year        = EXCLUDED.year,
    month       = EXCLUDED.month,
    month_name  = EXCLUDED.month_name,
    day_of_week = EXCLUDED.day_of_week,
    is_weekend  = EXCLUDED.is_weekend,
    season      = EXCLUDED.season;

-- name: upsert_fact
INSERT INTO fact_daily_weather (
    city_id, weather_date, temp_max, temp_min, temp_avg,
    precipitation, rain, wind_max, is_rainy_day
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (city_id, weather_date) DO UPDATE SET
    temp_max      = EXCLUDED.temp_max,
    temp_min      = EXCLUDED.temp_min,
    temp_avg      = EXCLUDED.temp_avg,
    precipitation = EXCLUDED.precipitation,
    rain          = EXCLUDED.rain,
    wind_max      = EXCLUDED.wind_max,
    is_rainy_day  = EXCLUDED.is_rainy_day;

-- name: upsert_watermark
INSERT INTO etl_watermark (city_id, last_date_loaded, updated_at)
VALUES (%s, %s, NOW())
ON CONFLICT (city_id) DO UPDATE SET
    last_date_loaded = EXCLUDED.last_date_loaded,
    updated_at       = NOW();


INSERT INTO rejected_records (town_name, observation_date, reject_reason)
VALUES (%s, %s, %s);

-- name: insert_run_log
INSERT INTO etl_run_log (
    start_time, end_time, rows_extracted, rows_loaded,
    rows_rejected, status, error_message
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
RETURNING run_id;
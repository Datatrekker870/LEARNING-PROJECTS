# Kenya City Weather Pipeline
### Multi-source, incremental ETL into a PostgreSQL star schema

---

## 📋 Project Overview

| | |
|---|---|
| **Level** | Beginner-plus. Builds directly on the API-to-PostgreSQL users pipeline. |
| **Tools** | Python, requests, psycopg2, python-dotenv, PostgreSQL on Aiven, Linux/PowerShell commands, VS Code |
| **Theory links** | Part 2 (ETL), OLTP vs OLAP, star schemas, incremental loading & watermarks, idempotency, data quality, error handling & logging |
| **Duration** | 5 weeks — one milestone per week |

# 1. The Business Scenario

A Kenyan agricultural advisory company wants to give farmers and county officers weather insights for major towns. Today, staff look up weather websites by hand — one town and one day at a time. The team wants a database they can query to answer questions like:

- "What was the average rainfall in Nakuru last week?"
- "Which towns are forecast to exceed 30°C tomorrow?"
- "How accurate was last week's forecast compared to what actually happened?"

Your job is to build an automated, incremental ETL pipeline that pulls weather data from multiple sources into a PostgreSQL star schema so those questions can be answered with a single SQL query.

# 2. What You Will Build

By the end of the project you will have:

- **A multi-source ingestion layer** — at least two weather data sources (e.g. Open-Meteo, OpenWeatherMap) called via `requests`.

- **A star schema in PostgreSQL** containing:
  - **Fact table(s)** — e.g. `fact_weather_observation` (daily/hourly readings)
  - **Dimension tables** — e.g. `dim_city`, `dim_date`, `dim_source`

- **Incremental loading logic** — using a watermark table so the pipeline only pulls new records on each run.

- **Idempotent loads** — re-running the pipeline for the same date range must not duplicate data (`ON CONFLICT` / upserts).

- **Data quality checks** — reject or flag missing values, impossible temperatures, out-of-range rainfall, duplicate keys.

- **Structured logging & error handling** — log every run, capture API failures, retry with backoff, and exit with meaningful status codes.

- **A query-ready warehouse** — sample analytical SQL queries answering the business questions above.

---

# 3. Architecture

The pipeline runs as four sequential phases inside `pipeline.py`, each in its own module:

## Phase summary

| Phase | Module | Entry point | Output |
|-------|--------|-------------|--------|
| 1. Geocode | `extract.py` | `build_dim_city()` | `dim_city` rows + `town → city_id` lookup |
| 2. Extract | `extract.py` | `extract_all_towns()` | `{town: [raw hourly rows]}` |
| 3. Transform | `transform.py` | `transform()` | `{accepted, rejected, dim_date}` |
| 4. Load | `load.py` | `load_all()` | Single committed transaction + `run_id` |

## Failure handling

- **Per-town isolation** — a geocode or extraction failure on one town is logged and skipped; the run continues with remaining towns.
- **Retries with backoff** — `get_json()` retries on `ConnectionError`, `Timeout`, and HTTP 5xx (1s → 2s → 4s). HTTP 4xx fails fast.
- **Atomic load** — `load_all()` wraps all writes in a single `conn` transaction. Any exception rolls everything back, leaving the DB unchanged.
- **Surviving failure log** — if the load rolls back, `write_failure_log()` writes a `FAILED` row to `etl_run_log` in its own transaction, so failed runs are still recorded.


**Key design decisions**

| Decision | Rationale |
|---|---|
| **Per-town failure isolation** in extract | One bad town doesn't kill the whole run — the other towns still load. |
| **Single-transaction load** | Facts, dims, watermarks, and the run-log row either all commit or all roll back. No partial state. |
| **Watermarks derived from `fact_records`** (not from caller-supplied dates) | Guarantees the watermark never outruns the data actually loaded. A town whose rows were all rejected never advances. |
| **Watermark = last *loaded* date, not last *attempted* date** | Prevents permanent data loss when an API returns empty or a date range is skipped. |
| **Idempotent upserts** on `(city_id, weather_date)` | Re-running is safe; a backfill overwrites the same keys. |
| **Rejected rows preserved** in `rejected_records` with the rejection reason | Data-quality issues are auditable without re-running extraction. |
| **Two-transaction failure handling** | The main load rolls back on error; `write_failure_log()` writes a `FAILED` row in a separate transaction so failures are never silently lost. |

---

# 4. Repository Layout

**Cross-file contracts** (important — these are how the modules agree with each other):

| Contract | Produced by | Consumed by |
|---|---|---|
| `{town_name: city_id}` lookup | `pipeline.build_dim_city()` | `pipeline.attach_city_id()`, `load._load_fact()` |
| Raw hourly records carry `observation_time` in **local (Africa/Nairobi) time** | `extract.extract_historical_for_town()` | `transform.aggregate_hourly_to_daily()` |
| Accepted records carry `city_id`, `observation_date`, daily aggregates | `pipeline.attach_city_id()` | `load._load_fact()` |
| Rejected records carry `{**raw, reject_reason}` | `transform.validate_and_split()` | `load._insert_rejected()` |
| `dim_date` covers **all** dates seen, including rejected ones | `transform.transform()` | `load._load_dim_date()` (FK requirement) |

---

# 5. Star Schema

## Table reference

| Table | Type | Purpose |
|-------|------|---------|
| `dim_city` | Dimension | One row per geocoded Kenyan town |
| `dim_date` | Dimension | Calendar lookup (year, month, weekday, Kenyan season) |
| `fact_daily_weather` | Fact | One row per (city, date) with aggregated daily weather |
| `etl_watermark` | Control | Last successfully loaded date per city (incremental loads) |
| `rejected_records` | Quality | Rows that failed validation, with the reason |
| `etl_run_log` | Monitoring | One row per pipeline run with status and row counts |


**Why a star schema?** The fact table stores one row per `(city, day)`. Queries like "average rainfall in Nakuru last week" become a two-table join (`fact_daily_weather` + `dim_date`); "which towns exceeded 30°C" is a filter on `temp_max`. Dimensions carry descriptive attributes that would otherwise be redundantly repeated on every fact row.

---

# 6. Configuration (`config.ini`)

```ini
[DATABASE]
host     = your-aiven-host.aivencloud.com
port     = 12345
dbname   = defaultdb
user     = avnadmin
password = <from-environment-or-secret-manager>
sslmode  = require

[API]
towns                 = Nairobi, Mombasa, Kisumu, Nakuru, Eldoret
hourly_vars           = temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code
timezone              = Africa/Nairobi
historical_start_date = 2026-01-01
data_lag_days         = 4

[PIPELINE]
request_timeout = 30
max_retries     = 3
log_level       = INFO
log_file        = pipeline.log





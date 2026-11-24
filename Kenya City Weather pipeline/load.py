# load.py
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
DEFAULT_SQL_PATH = PROJECT_ROOT / "sql" / "create_tables.sql"


# ----------------------------------------------------------------------
# SQL file parser
# ----------------------------------------------------------------------
def _parse_sql_file(path: Path | str | None = None) -> tuple[str, dict]:
    """
    Split the SQL file into:
      - ddl: everything up to the "UPSERTS" marker
      - upserts: dict mapping name -> statement text

    Named UPSERTs are marked with a leading line:
        -- name: <identifier>
    """
    # Accept absolute paths, paths relative to project root, or a bare filename.
    if path is None:
        sql_path = DEFAULT_SQL_PATH
    else:
        p = Path(path)
        sql_path = p if p.is_absolute() else PROJECT_ROOT / p

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        raw = f.read()

    # Flexible marker: any number of '=' chars, any whitespace.
    marker_re = re.compile(r"--\s*=+\s*\n--\s*UPSERTS\b", re.MULTILINE)
    m = marker_re.search(raw)
    if not m:
        raise RuntimeError(f"UPSERTS marker not found in {sql_path}")
    ddl = raw[: m.start()]
    upsert_block = raw[m.end():]

    upserts: dict[str, str] = {}
    # Names may contain word chars, hyphens, and dots.
    pattern = re.compile(
        r"--\s*name:\s*([\w.-]+)\s*\n(.*?)(?=\n--\s*name:|\Z)",
        re.DOTALL,
    )
    for match in pattern.finditer(upsert_block):
        name = match.group(1)
        sql = match.group(2).strip().rstrip(";") + ";"
        upserts[name] = sql

    return ddl, upserts


# Lazy-loaded SQL, so an import-time failure doesn't break the module.
_DDL: Optional[str] = None
_UPSERTS: Optional[dict[str, str]] = None


def _ensure_sql_loaded(sql_path: Path | str | None = None) -> None:
    global _DDL, _UPSERTS
    if _DDL is None or _UPSERTS is None:
        _DDL, _UPSERTS = _parse_sql_file(sql_path)


def _upserts() -> dict[str, str]:
    _ensure_sql_loaded()
    assert _UPSERTS is not None
    return _UPSERTS


# ----------------------------------------------------------------------
# Table creation
# ----------------------------------------------------------------------
def create_tables(conn, sql_path: Path | str | None = None):
    """
    Execute the DDL block of the SQL file (idempotent).
    Path resolution: absolute, or relative to project root, or default
    `sql/create_tables.sql` next to load.py.
    """
    _ensure_sql_loaded(sql_path)
    assert _DDL is not None
    with conn:  # consistent with load_all: commits on success
        with conn.cursor() as cur:
            cur.execute(_DDL)
    logger.info("Tables created/verified from SQL file")


# ----------------------------------------------------------------------
# Individual loaders (each uses only named UPSERTs from the SQL file)
# ----------------------------------------------------------------------
def _load_dim_city(cur, cities: list[dict]):
    sql = _upserts()["upsert_city"]
    for c in cities:
        cur.execute(sql, (
            c["city_id"], c["name"], c.get("county"),
            c["latitude"], c["longitude"],
            c.get("elevation"), c.get("population"),
        ))
    logger.info(f"Upserted {len(cities)} rows into dim_city")


def _load_dim_date(cur, dim_date: dict):
    sql = _upserts()["upsert_date"]
    month_names = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    count = 0
    for iso, d in dim_date.items():
        month = d["month"]
        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month {month!r} for date {iso!r}")
        # NOTE: day_of_week is 1=Mon..7=Sun (isoweekday), matching
        # transform.build_dim_date. Weekend = 6 or 7.
        dow = d["day_of_week"]
        cur.execute(sql, (
            iso, d["year"], month, month_names[month],
            dow, dow >= 6, d["season"],
        ))
        count += 1
    logger.info(f"Upserted {count} rows into dim_date")


def _load_fact(cur, records: list[dict], town_to_city: dict[str, int]):
    sql = _upserts()["upsert_fact"]
    count = 0
    for r in records:
        # Resolve city_id: prefer an explicit value, else map from town_name.
        city_id = r.get("city_id")
        if city_id is None:
            town = r.get("town_name")
            city_id = town_to_city.get(town) if town else None
        if city_id is None:
            # Fail loudly: a fact row with no city is an upstream bug.
            raise ValueError(
                f"No city_id for town {r.get('town_name')!r} "
                f"(known towns: {sorted(town_to_city)[:10]}...)"
            )

        precip = r.get("precipitation_sum")
        cur.execute(sql, (
            city_id,
            r["observation_date"],
            r.get("temperature_2m_max"),
            r.get("temperature_2m_min"),
            r.get("average_temperature"),
            precip,                    # precipitation_sum column
            precip,                    # rain column (all precip counted as rain)
            r.get("wind_max"),         # nullable
            bool(r.get("is_rainy_day")),
        ))
        count += 1
    logger.info(f"Upserted {count} rows into fact_daily_weather")


def _derive_watermarks(fact_records: list[dict]) -> list[dict]:
    """
    Watermark = the latest observation_date actually loaded, per city.

    Derived from fact_records (not from the caller) so a town whose rows
    were all rejected — and therefore has no facts — never advances its
    watermark. Towns that genuinely produced no new data are simply absent
    from fact_records and keep their previous watermark.
    """
    latest: dict[int, str] = {}
    for r in fact_records:
        cid = r.get("city_id")
        if cid is None:
            # Should not happen if _load_fact validated; skip defensively.
            continue
        d = r["observation_date"]
        if cid not in latest or d > latest[cid]:
            latest[cid] = d
    return [
        {"city_id": cid, "last_date_loaded": d}
        for cid, d in latest.items()
    ]


def _update_watermarks(cur, watermarks: list[dict]):
    if not watermarks:
        logger.info("No watermarks to update")
        return
    sql = _upserts()["upsert_watermark"]
    for w in watermarks:
        cur.execute(sql, (w["city_id"], w["last_date_loaded"]))
    logger.info(f"Upserted {len(watermarks)} rows into etl_watermark")


def _insert_rejected(cur, rejected: list[dict]):
    """
    Persist rejected rows.

    Bind order matches sql/create_tables.sql:
        (town_name, observation_date, reject_reason)
    """
    if not rejected:
        return
    sql = _upserts()["insert_rejected"]
    for r in rejected:
        cur.execute(sql, (
            r.get("town_name"),
            r.get("observation_date"),
            r.get("reject_reason", "unknown"),
        ))
    logger.info(f"Inserted {len(rejected)} rows into rejected_records")


# ----------------------------------------------------------------------
# SINGLE-TRANSACTION LOAD
# ----------------------------------------------------------------------
def load_all(
    conn,
    cities: list[dict],
    dim_date: dict,
    fact_records: list[dict],
    rejected: list[dict],
    run_start: datetime,
    rows_extracted: int,
) -> Optional[int]:
    """
    Load everything in ONE transaction — dim_city → dim_date → fact_daily_weather
    → etl_watermark (+ rejected_records, etl_run_log).

    On any exception the transaction is rolled back, nothing is persisted,
    and the exception propagates. The caller is expected to call
    write_failure_log() in its except block.

    Watermarks are derived internally from fact_records; callers do not
    supply them. This guarantees the watermark never outruns the facts.

    Returns the run_id from etl_run_log (or None if the RETURNING clause
    didn't produce a row).
    """
    town_to_city = {c["name"]: c["city_id"] for c in cities}
    watermarks = _derive_watermarks(fact_records)

    run_id: Optional[int] = None
    try:
        with conn:  # commits on success, rolls back on exception
            with conn.cursor() as cur:
                _load_dim_city(cur, cities)
                _load_dim_date(cur, dim_date)
                _load_fact(cur, fact_records, town_to_city)
                _update_watermarks(cur, watermarks)
                _insert_rejected(cur, rejected)

                cur.execute(_upserts()["insert_run_log"], (
                    run_start, datetime.now(timezone.utc),
                    rows_extracted, len(fact_records),
                    len(rejected), "SUCCESS", None,
                ))
                row = cur.fetchone()
                run_id = row[0] if row else None

        logger.info(f"Transaction committed. run_id={run_id}")
        return run_id

    except Exception as e:
        logger.error(f"Load transaction rolled back: {e}", exc_info=True)
        raise


# ----------------------------------------------------------------------
# FAILURE LOG (separate transaction, survives rollback of load_all)
# ----------------------------------------------------------------------
def write_failure_log(
    conn,
    run_start: datetime,
    rows_extracted: int,
    rows_rejected: int,
    error_message: str,
) -> Optional[int]:
    """
    Persist a FAILED row to etl_run_log in its own transaction, so it
    survives even when the main load rolled back.

    Consumes the RETURNING result (if any) so the cursor is left in a
    clean state, and returns the run_id.
    """
    upserts = _upserts()
    run_id: Optional[int] = None
    with conn:
        with conn.cursor() as cur:
            cur.execute(upserts["insert_run_log"], (
                run_start,
                datetime.now(timezone.utc),
                rows_extracted,
                0,
                rows_rejected,
                "FAILED",
                error_message,
            ))
            row = cur.fetchone()
            run_id = row[0] if row else None
    logger.info(f"Logged FAILED run. run_id={run_id}")
    return run_id
# pipeline.py
import logging
import sys
from configparser import ConfigParser
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from extract import extract_all_towns, geocode_town
from transform import transform
from load import create_tables, load_all, write_failure_log

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
def setup_logging(config):
    log_level = config.get("PIPELINE", "log_level", fallback="INFO")
    log_file = config.get("PIPELINE", "log_file", fallback="pipeline.log")
    log_path = PROJECT_ROOT / log_file
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path),
        ],
    )
    return logging.getLogger("pipeline")


# ----------------------------------------------------------------------
# Config loading
# ----------------------------------------------------------------------
def load_config() -> ConfigParser:
    config_path = PROJECT_ROOT / "config.ini"
    if not config_path.exists():
        raise FileNotFoundError(f"config.ini not found at {config_path}")

    config = ConfigParser()
    if not config.read(config_path, encoding="utf-8"):
        raise RuntimeError(f"Failed to read {config_path}")

    missing = {"DATABASE", "API", "PIPELINE"} - set(config.sections())
    if missing:
        raise RuntimeError(
            f"config.ini is missing sections: {missing}. "
            f"Found: {config.sections()}"
        )
    return config


# ----------------------------------------------------------------------
# DB connection
# ----------------------------------------------------------------------
def get_connection(config):
    import psycopg2
    return psycopg2.connect(
        host=config.get("DATABASE", "host"),
        port=config.get("DATABASE", "port", fallback="5432"),
        dbname=config.get("DATABASE", "dbname"),
        user=config.get("DATABASE", "user"),
        password=config.get("DATABASE", "password"),
        sslmode=config.get("DATABASE", "sslmode", fallback="prefer"),
    )


# ----------------------------------------------------------------------
# Watermark read (writes happen inside load_all's transaction)
# ----------------------------------------------------------------------
def read_watermark(conn, town_name: str) -> date | None:
    """
    Returns the last loaded date for a town as a `date`, or None if never
    loaded. Coerces whatever the driver returns (date, datetime, or ISO
    string) so downstream arithmetic (`wm + timedelta(days=1)`) works.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT w.last_date_loaded "
            "FROM etl_watermark w "
            "JOIN dim_city c ON c.city_id = w.city_id "
            "WHERE c.name = %s",
            (town_name,),
        )
        row = cur.fetchone()
    if not row or row[0] is None:
        return None
    v = row[0]
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v)[:10])


# ----------------------------------------------------------------------
# Geocode + build dim_city rows (one call per town, isolated)
# ----------------------------------------------------------------------
def build_dim_city(config, towns: list[str]) -> tuple[list[dict], dict]:
    """
    Geocode each town once via extract.geocode_town, which now returns
    city_id / elevation / population alongside lat/lon and admin1.

    Returns:
      - dim_city rows (for load_all)
      - lookup {town_name: {city_id, latitude, longitude, county, elevation, population}}
    Failures are logged and skipped; the town is absent from both outputs.
    """
    rows: list[dict] = []
    lookup: dict[str, dict] = {}

    for town in towns:
        try:
            geo = geocode_town(town, config)
            city_id = geo.get("city_id")
            if city_id is None:
                raise ValueError(f"geocoder returned no id for {town!r}")

            meta = {
                "city_id": city_id,
                "latitude": geo["latitude"],
                "longitude": geo["longitude"],
                "county": geo.get("admin1") or None,
                "elevation": geo.get("elevation"),
                "population": geo.get("population"),
            }
            lookup[town] = meta
            rows.append({
                "city_id": city_id,
                "name": town,
                "county": meta["county"],
                "latitude": meta["latitude"],
                "longitude": meta["longitude"],
                "elevation": meta["elevation"],
                "population": meta["population"],
            })
            logger.info(f"Geocoded {town} -> city_id={city_id}")

        except Exception as e:
            logger.error(f"Geocoding failed for {town}: {e}. Skipping.")

    return rows, lookup


# ----------------------------------------------------------------------
# Attach city_id to fact records (transform output -> fact schema)
# ----------------------------------------------------------------------
def attach_city_id(records: list[dict], lookup: dict) -> list[dict]:
    """
    Add city_id to each accepted record by joining on town_name.
    Drops any record whose town was never geocoded, logging the town names.
    """
    out: list[dict] = []
    dropped_by_town: dict[str, int] = {}
    for r in records:
        town = r.get("town_name")
        meta = lookup.get(town)
        if not meta:
            dropped_by_town[town] = dropped_by_town.get(town, 0) + 1
            continue
        out.append({**r, "city_id": meta["city_id"]})
    if dropped_by_town:
        logger.warning(
            f"Dropped fact records with no geocoded town: {dropped_by_town}"
        )
    return out


# ----------------------------------------------------------------------
# Watermarks are derived inside load_all() from the facts actually
# loaded. pipeline.py does NOT pass a watermarks argument — that
# guarantees the watermark never outruns the facts, and a town whose
# rows were all rejected never advances its watermark.
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main() -> int:
    config = load_config()
    setup_logging(config)

    logger.info("=" * 60)
    logger.info("Kenya Weather Pipeline started")
    logger.info("=" * 60)

    towns = [t.strip() for t in config.get("API", "towns").split(",") if t.strip()]
    data_lag = config.getint("API", "data_lag_days", fallback=1)
    run_start = datetime.now(timezone.utc)

    rows_extracted = 0
    fact_records: list[dict] = []
    rejected: list[dict] = []

    try:
        conn = get_connection(config)
    except Exception as e:
        logger.error(f"DB connection failed: {e}", exc_info=True)
        return 1

    try:
        # ---- 0. Ensure schema (inside try so failures hit the failure log) ----
        sql_rel = config.get(
            "PIPELINE", "create_tables_sql", fallback="sql/create_tables.sql"
        )
        create_tables(conn, PROJECT_ROOT / sql_rel)

        # ---- 1. Geocode (builds dim_city + city_id lookup) ----
        logger.info("--- GEOCODING phase ---")
        dim_city_rows, lookup = build_dim_city(config, towns)
        if not lookup:
            raise RuntimeError("No towns geocoded; aborting run")

        # ---- 2. Extract (per-town watermark, per-town failure isolation) ----
        logger.info("--- EXTRACT phase ---")
        raw_by_town = extract_all_towns(
            config,
            get_watermark=lambda town: read_watermark(conn, town),
        )

        # Surface towns that were extracted but won't be loadable.
        unloadable = set(raw_by_town) - set(lookup)
        if unloadable:
            logger.warning(
                f"Towns extracted but not geocoded (will be dropped): "
                f"{sorted(unloadable)}"
            )

        raw_flat = [r for rows in raw_by_town.values() for r in rows]
        rows_extracted = len(raw_flat)
        logger.info(
            f"Extracted {rows_extracted} raw records across "
            f"{len(raw_by_town)} towns"
        )

        # ---- 3. Transform ----
        logger.info("--- TRANSFORM phase ---")
        transformed = transform(raw_flat)
        dim_date = transformed["dim_date"]
        rejected = transformed["rejected"]

        # Attach city_id before load (fact FK requirement)
        fact_records = attach_city_id(transformed["accepted"], lookup)
        logger.info(
            f"Prepared {len(fact_records)} fact rows, {len(rejected)} rejected"
        )

        # ---- 4. Load (single transaction; watermarks derived internally) ----
        logger.info("--- LOAD phase ---")
        run_id = load_all(
            conn=conn,
            cities=dim_city_rows,
            dim_date=dim_date,
            fact_records=fact_records,
            rejected=rejected,
            run_start=run_start,
            rows_extracted=rows_extracted,
        )
        logger.info(f"Load committed. run_id={run_id}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        # Log the failed run outside the rolled-back transaction.
        try:
            write_failure_log(
                conn=conn,
                run_start=run_start,
                rows_extracted=rows_extracted,
                rows_rejected=len(rejected),
                error_message=str(e),
            )
        except Exception as log_err:
            logger.error(f"Could not write failure run log: {log_err}")
        return 1

    finally:
        conn.close()

    logger.info("=" * 60)
    logger.info("Pipeline finished successfully")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
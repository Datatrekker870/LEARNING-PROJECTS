# transform.py
import logging
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Tunables (previously hardcoded magic numbers)
# ----------------------------------------------------------------------
RAINY_DAY_THRESHOLD_MM = 1.0
TEMP_MIN_ALLOWED = -5.0
TEMP_MAX_ALLOWED = 50.0


# ----------------------------------------------------------------------
# Kenyan season lookup (used when building dim_date)
# ----------------------------------------------------------------------
def kenyan_season(month: int) -> str:
    """
    Long rains: Mar-May
    Short rains: Oct-Dec
    Dry season: all other months
    """
    if 3 <= month <= 5:
        return "Long rains"
    if 10 <= month <= 12:
        return "Short rains"
    return "Dry season"


# ----------------------------------------------------------------------
# AGGREGATE: hourly -> daily
# ----------------------------------------------------------------------
def aggregate_hourly_to_daily(records):
    """
    Collapse hourly records into one row per (town, date) with:
      temperature_2m_max, temperature_2m_min, precipitation_sum, wind_max.

    Input records carry `observation_time` (ISO hourly string).

    IMPORTANT: this function assumes `observation_time` is already expressed
    in the local timezone of the target location (i.e. extract.py must query
    Open-Meteo with `timezone=Africa/Nairobi` or equivalent, NOT `UTC`).
    If that assumption is ever broken, a local "day" can be split across
    two bucket dates and daily aggregates will be silently wrong.
    """
    buckets = {}
    skipped = 0

    for r in records:
        ts = r.get("observation_time")
        if not ts:
            skipped += 1
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except (TypeError, ValueError):
            skipped += 1
            continue

        key = (r["town_name"], dt.date().isoformat())
        b = buckets.setdefault(key, {
            "town_name": r["town_name"],
            "observation_date": dt.date().isoformat(),
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "temps": [],
            "precips": [],
            "winds": [],
        })
        if r.get("temperature_2m") is not None:
            b["temps"].append(r["temperature_2m"])
        if r.get("precipitation") is not None:
            b["precips"].append(r["precipitation"])
        if r.get("wind_speed_10m") is not None:
            b["winds"].append(r["wind_speed_10m"])

    if skipped:
        logger.warning(
            f"aggregate_hourly_to_daily: dropped {skipped} rows with "
            f"missing/unparseable observation_time"
        )

    daily = []
    for b in buckets.values():
        daily.append({
            "town_name": b["town_name"],
            "observation_date": b["observation_date"],
            "latitude": b["latitude"],
            "longitude": b["longitude"],
            "temperature_2m_max": max(b["temps"]) if b["temps"] else None,
            "temperature_2m_min": min(b["temps"]) if b["temps"] else None,
            "precipitation_sum": sum(b["precips"]) if b["precips"] else None,
            "wind_max": max(b["winds"]) if b["winds"] else None,
        })
    return daily


# ----------------------------------------------------------------------
# DERIVE + ROUND
# ----------------------------------------------------------------------
def derive_and_round(record: dict) -> dict:
    """
    Add derived fields and round all decimals to 1 decimal place.
      - average_temperature = (max + min) / 2
      - is_rainy_day = precipitation_sum >= RAINY_DAY_THRESHOLD_MM

    Returns a NEW dict; does not mutate the input.
    """
    out = dict(record)

    def r1(x):
        return round(x, 1) if isinstance(x, (int, float)) else None

    tmax_r = r1(out.get("temperature_2m_max"))
    tmin_r = r1(out.get("temperature_2m_min"))
    precip_r = r1(out.get("precipitation_sum"))

    out["temperature_2m_max"] = tmax_r
    out["temperature_2m_min"] = tmin_r
    out["precipitation_sum"] = precip_r
    out["wind_max"] = r1(out.get("wind_max"))

    out["average_temperature"] = (
        round((tmax_r + tmin_r) / 2, 1)
        if isinstance(tmax_r, (int, float)) and isinstance(tmin_r, (int, float))
        else None
    )
    # Computed from the ROUNDED value so it's internally consistent.
    out["is_rainy_day"] = (
        (precip_r is not None) and (precip_r >= RAINY_DAY_THRESHOLD_MM)
    )
    return out


# ----------------------------------------------------------------------
# DIM_DATE
# ----------------------------------------------------------------------
def build_dim_date(dates: list[date]) -> dict[str, dict]:
    """
    Build a dim_date lookup keyed by ISO date string. Includes the Kenyan
    season. Pure Python, no external deps.

    Accepts `date` objects only. `datetime` instances are coerced to `date`
    so they don't produce keys with a time component.
    """
    dim: dict[str, dict] = {}
    for d in dates:
        if isinstance(d, datetime):
            d = d.date()
        iso = d.isoformat()
        if iso in dim:
            continue
        dim[iso] = {
            "date": iso,
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "day_of_week": d.isoweekday(),      # 1=Mon ... 7=Sun
            "season": kenyan_season(d.month),
        }
    return dim


# ----------------------------------------------------------------------
# VALIDATE
# ----------------------------------------------------------------------
def validate_and_split(
    daily_records: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Split records into accepted and rejected.
    A record is rejected (with a reason) if ANY of these rules fire:
      1. required value missing (temperature_2m_max, min, or precipitation_sum is null)
      2. max temperature < min temperature
      3. any temperature outside [TEMP_MIN_ALLOWED, TEMP_MAX_ALLOWED] °C
      4. precipitation is negative
      5. same (town, date) appears more than once in this batch
         (first occurrence is kept, subsequent ones rejected)

    Note: `wind_max` is intentionally NOT required (nullable by design).
    """
    accepted: list[dict] = []
    rejected: list[dict] = []

    seen_keys: set[tuple[str, str]] = set()

    for rec in daily_records:
        reasons: list[str] = []

        tmax = rec.get("temperature_2m_max")
        tmin = rec.get("temperature_2m_min")
        precip = rec.get("precipitation_sum")
        key = (rec.get("town_name"), rec.get("observation_date"))

        # Rule 1: required value missing
        if tmax is None:
            reasons.append("temperature_2m_max is null")
        if tmin is None:
            reasons.append("temperature_2m_min is null")
        if precip is None:
            reasons.append("precipitation_sum is null")

        # Rule 2: max below min
        if (
            isinstance(tmax, (int, float))
            and isinstance(tmin, (int, float))
            and tmax < tmin
        ):
            reasons.append(
                f"max temperature {tmax}°C is below min temperature {tmin}°C"
            )

        # Rule 3: temperature outside allowed range
        for label, val in (("max", tmax), ("min", tmin)):
            if isinstance(val, (int, float)) and not (
                TEMP_MIN_ALLOWED <= val <= TEMP_MAX_ALLOWED
            ):
                reasons.append(
                    f"{label} temperature {val}°C outside "
                    f"{TEMP_MIN_ALLOWED}..{TEMP_MAX_ALLOWED}°C"
                )

        # Rule 4: negative precipitation
        if isinstance(precip, (int, float)) and precip < 0:
            reasons.append(f"precipitation {precip} mm is negative")

        # Rule 5: duplicate in batch (keep first, reject the rest)
        if key in seen_keys:
            reasons.append(
                f"duplicate town+date in batch: {key[0]} {key[1]}"
            )
        else:
            seen_keys.add(key)

        if reasons:
            rejected.append({**rec, "reject_reason": "; ".join(reasons)})
        else:
            accepted.append(rec)

    logger.info(
        f"Validation: accepted={len(accepted)}, rejected={len(rejected)}"
    )
    return accepted, rejected


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------
def transform(raw_records: list[dict]) -> dict:
    """
    Full transform phase. Returns a dict:
      {
        "accepted": [ {..daily record..} ],
        "rejected": [ {..original + reject_reason..} ],
        "dim_date": { iso_date: {..} },
      }
    """
    if not raw_records:
        logger.info("transform: no raw records; returning empty result")
        return {"accepted": [], "rejected": [], "dim_date": {}}

    # Collapse hourly rows into one row per (town, date).
    # aggregate_hourly_to_daily already guarantees uniqueness of
    # (town_name, observation_date) within its output, so no separate
    # reshape/dedupe step is needed here.
    daily_records = aggregate_hourly_to_daily(raw_records)

    enriched = [derive_and_round(r) for r in daily_records]

    # Build dim_date from all dates seen in this batch
    parsed_dates: list[date] = []
    for r in enriched:
        obs = r.get("observation_date")
        if isinstance(obs, str):
            try:
                parsed_dates.append(date.fromisoformat(obs))
            except ValueError:
                pass
    dim_date = build_dim_date(parsed_dates)

    accepted, rejected = validate_and_split(enriched)
    return {"accepted": accepted, "rejected": rejected, "dim_date": dim_date}

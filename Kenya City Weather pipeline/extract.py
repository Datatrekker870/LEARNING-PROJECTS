# extract.py
import requests
import time
import logging
from datetime import date, timedelta
from configparser import ConfigParser
from typing import Callable, Optional

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"


# ----------------------------------------------------------------------
# Reusable HTTP helper with exponential backoff (1s, 2s, 4s)
# ----------------------------------------------------------------------
def get_json(url, params, timeout=30, max_retries=3):
    """
    GET a URL and return parsed JSON.

    Retries with exponential backoff on:
      - ConnectionError
      - Timeout
      - HTTP 5xx responses

    Does NOT retry on 4xx (bad request) — those raise immediately.

    Backoff between attempts: 1s -> 2s -> 4s (i.e. 2**attempt).
    Raises the last exception if all retries are exhausted.
    """
    if max_retries < 1:
        raise ValueError(f"max_retries must be >= 1, got {max_retries}")

    last_exc = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code >= 500:
                err = requests.HTTPError(
                    f"Server error {resp.status_code} for {url}", response=resp
                )
                raise err
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            # 4xx: fail fast, do not retry
            if e.response is not None and 400 <= e.response.status_code < 500:
                logger.error(f"Client error {e.response.status_code} for {url}: {e}")
                raise
            last_exc = e
        except (requests.ConnectionError, requests.Timeout) as e:
            last_exc = e

        if attempt < max_retries - 1:
            wait = 2 ** attempt  # 1, 2, 4
            logger.warning(
                f"Request failed (attempt {attempt + 1}/{max_retries}): {last_exc}. "
                f"Retrying in {wait}s..."
            )
            time.sleep(wait)

    logger.error(f"All {max_retries} attempts failed for {url}: {last_exc}")
    raise last_exc


# ----------------------------------------------------------------------
# Geocoding (filtered to Kenya)
# ----------------------------------------------------------------------
def geocode_town(town_name, config):
    """
    Geocode a single Kenyan town. Returns dict:
      {town_name, latitude, longitude, admin1}
    Raises ValueError if no result found.
    """
    params = {
        "name": town_name,
        "count": 1,
        "language": "en",
        "format": "json",
        "countryCode": "KE",
    }
    data = get_json(
        GEOCODING_URL,
        params,
        timeout=config.getint("PIPELINE", "request_timeout", fallback=30),
        max_retries=config.getint("PIPELINE", "max_retries", fallback=3),
    )
    results = data.get("results")
    if not results:
        raise ValueError(f"No geocoding result for '{town_name}' in Kenya")

    r = results[0]
    return {
    "town_name": town_name,
    "latitude": r["latitude"],
    "longitude": r["longitude"],
    "admin1": r.get("admin1", ""),
    "city_id": r.get("id"),              # <- must be here
    "elevation": r.get("elevation"),
    "population": r.get("population")

    }


# ----------------------------------------------------------------------
# Historical weather for a single geocoded town
# ----------------------------------------------------------------------
def extract_historical_for_town(geo, start_date, end_date, config):
    """
    Fetch hourly weather for one town between start_date and end_date (inclusive).
    Returns a list of raw record dicts.
    """
    params = {
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": config.get("API", "hourly_vars"),
        "timezone": config.get("API", "timezone", fallback="Africa/Nairobi"),
    }
    data = get_json(
        HISTORICAL_URL,
        params,
        timeout=config.getint("PIPELINE", "request_timeout", fallback=30),
        max_retries=config.getint("PIPELINE", "max_retries", fallback=3),
    )

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    n = len(times)

    if n == 0:
        logger.warning(
            f"[{geo['town_name']}] API returned no hourly data "
            f"for {start_date}..{end_date}"
        )
        return []

    def col(name):
        values = hourly.get(name)
        if not values:
            return [None] * n
        if len(values) < n:
            logger.warning(
                f"[{geo['town_name']}] column '{name}' has {len(values)} "
                f"values but {n} timestamps; padding with None"
            )
            values = list(values) + [None] * (n - len(values))
        return values[:n]

    temps = col("temperature_2m")
    rh = col("relative_humidity_2m")
    precip = col("precipitation")
    wind = col("wind_speed_10m")
    wcode = col("weather_code")

    records = []
    for i, t in enumerate(times):
        records.append({
            "town_name": geo["town_name"],
            "observation_time": t,
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "temperature_2m": temps[i],
            "relative_humidity_2m": rh[i],
            "precipitation": precip[i],
            "wind_speed_10m": wind[i],
            "weather_code": wcode[i],
        })
    return records


# ----------------------------------------------------------------------
# Orchestration: geocode once, then per-town extraction with isolation
# ----------------------------------------------------------------------
def extract_all_towns(config: ConfigParser, get_watermark: Callable[[str], Optional[date]]):
    """
    Runs the full extraction phase.

    Args:
        config: parsed ConfigParser (reads API.towns, API.data_lag_days, etc.)
        get_watermark: callable(town_name) -> date | None
                       Returns the last successfully extracted date for a town,
                       or None if the town has never been extracted.

    Returns:
        dict[str, list[dict]] mapping town_name -> raw records.
        Towns that failed are simply absent from the dict.
        Towns with nothing to fetch are present with an empty list.

    Behaviour:
        - Each town is geocoded once, before its extraction call.
        - Date range per town: (watermark + 1 day) -> (today - data_lag_days).
        - If watermark is None, start from API.historical_start_date
          (default 2026-01-01).
        - A failure on one town (geocode or extract, after all retries) is
          logged and skipped — the loop continues with the remaining towns.
    """
    historical_start = date.fromisoformat(
        config.get("API", "historical_start_date", fallback="2026-01-01")
    )
    
    data_lag = config.getint("API", "data_lag_days", fallback=1)
    towns_raw = config.get("API", "towns", fallback="")
    towns = [t.strip() for t in towns_raw.split(",") if t.strip()]

    if not towns:
        logger.warning("No towns configured under API.towns; nothing to do")
        return {}

   
    end_date = date.today() - timedelta(days=data_lag)
    logger.info(f"Extraction window end date (today - {data_lag}d): {end_date}")

    if historical_start > end_date:
        logger.warning(
            f"API.historical_start_date ({historical_start}) is after the "
            f"extraction end date ({end_date}); all towns will be skipped. "
            f"Check your config."
        )

    results: dict[str, list[dict]] = {}

    for town in towns:
        try:
            # Geocode once per town
            geo = geocode_town(town, config)
            logger.info(
                f"[{town}] Geocoded -> lat={geo['latitude']}, lon={geo['longitude']}"
            )

            # Resolve start date from watermark
            wm = get_watermark(town)
            if wm is None:
                start_date = historical_start
                logger.info(
                    f"[{town}] No watermark; backfilling from {start_date}"
                )
            else:
                start_date = wm + timedelta(days=1)
                logger.info(
                    f"[{town}] Watermark={wm}; requesting from {start_date}"
                )

            if start_date > end_date:
                logger.info(
                    f"[{town}] Already up to date (start={start_date} > end={end_date}); skipping"
                )
                results[town] = []
                continue

            # Fetch
            records = extract_historical_for_town(geo, start_date, end_date, config)
            logger.info(f"[{town}] Extracted {len(records)} raw records")
            results[town] = records

        except Exception as e:
            logger.error(f"[{town}] Extraction failed: {e}", exc_info=True)

    return results
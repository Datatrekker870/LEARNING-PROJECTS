"""
Day 1 - API Data Extraction and Transformation
Squad Python Specialization - Data Engineering

Fill in every function. Keep the signatures; you may add helpers of your own.
"""
import csv
import json
from pathlib import Path
from requests.exceptions import HTTPError, RequestException

import pandas as pd
import requests

API_URL = "https://jsonplaceholder.typicode.com/users"
OUTPUT_PATH = Path("output") / "customers_clean.csv"


def fetch_users(url: str = API_URL, timeout: float = 10.0) -> list[dict]:
    """Retrieve the list of users from the API.
    Must raise or report a clear error for: connection failures, timeouts,
    non-200 status codes and bodies that are not valid JSON.
    """
    try:
        response = requests.get(url, timeout=timeout)
    except RequestException as e:
        # Covers ConnectionError, Timeout, etc.
        raise RuntimeError(f"Request to {url} failed: {e}") from e

    # Raise a clear error for any non-200 status i.e 400 and 600
    if response.status_code != 200:
        raise HTTPError(
            f"Expected status 200 from {url}, got {response.status_code}",
            response=response,
        )

    # Guard against non-JSON bodies
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise ValueError(f"Response from {url} was not valid JSON: {e}") from e

    return data
    

def describe_structure(payload) -> None:
    """Print what Python data types the payload and one record are made of
    (the top-level container, a record, and each nested value)."""

    print(f"Top-level container: {type(payload).__name__} "
          f"(length: {len(payload)})")

    if not payload:
        print("  Payload is empty.")
        return

    record = payload[0]
    print(f"\nFirst record: {type(record).__name__}")
    for key, value in record.items():
        print(f"{key:<12} -> {type(value).__name__}  (value: {value!r})")
    


def extract_core_fields(users: list[dict]) -> list[dict]:
    """Return one small dict per user with id, name, email, city and company name."""
    
    result = []
    for user in users:
        result.append({
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "city": user["address"]["city"],       
            "company": user["company"]["name"],    
        })
    return result
    


def build_structures(users: list[dict]) -> tuple[list, list[tuple], dict]:
    """Return (list_of_names, list_of_(id, email)_tuples, dict_of_id_to_city).

    Use at least one list comprehension and one dict comprehension.
    """
    names = [u["name"] for u in users]                                    
    id_email_pairs = [(u["id"], u["email"]) for u in users]               
    id_to_city = {u["id"]: u["address"]["city"] for u in users}           
    return names, id_email_pairs, id_to_city
    


def flatten_user(user: dict, parent_key: str = "", sep: str = "_") -> dict:
    """Flatten one nested user record into a single-level dict.

    e.g. a nested address -> geo -> lat becomes the key address_geo_lat.
    """
    items = {}
    for key, value in user.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            
            items.update(flatten_user(value, new_key, sep=sep))
        elif isinstance(value, list):
            # Lists: either flatten indices or JSON-encode them
            # Simplest: JSON-encode so it fits in a CSV cell
            items[new_key] = json.dumps(value)
        else:
            items[new_key] = value
    return items

    
def to_dataframe(flat_users: list[dict]) -> pd.DataFrame:
    """Build a DataFrame with the columns in the expected-output order."""
    EXPECTED_COLUMNS = [
    "id", "name", "username", "email",
    "address_street", "address_suite", "address_city", "address_zipcode",
    "address_geo_lat", "address_geo_lng",
    "phone", "website",
    "company_name", "company_catchPhrase", "company_bs",
]
    df = pd.DataFrame(flat_users)
    # Reorder + ensure every column exists (fill missing with empty)
    return df.reindex(columns=EXPECTED_COLUMNS)



def export_csv(df: pd.DataFrame, path: Path = OUTPUT_PATH) -> Path:
    """Write the DataFrame to CSV (creating the folder if needed) and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)
    return path


def main() -> None:
    # TODO: wire the steps together and print a short run summary.
    users = fetch_users() # fetching data from api
    describe_structure(users) # check out what data types we have in in th data set

    core = extract_core_fields(users)
    names, id_email_pairs, id_to_city = build_structures(users)

    flat = [flatten_user(u) for u in users]
    df = to_dataframe(flat)
    out = export_csv(df)

    print(f"\nFetched {len(users)} users")
    print(f"First 3 names: {names[:3]}")
    print(f"First 3 (id, email) pairs: {id_email_pairs[:3]}")
    print(f"IDs mapped to cities: {id_to_city}")
    print(f"DataFrame shape: {df.shape}")
    print(f"CSV written to: {out.resolve()}")


if __name__ == "__main__":
    main()

# Day 1 — API Data Extraction and Transformation

A beginner-friendly Python script that pulls user data from a public REST API,
cleans it up, and saves it as a CSV file. This is the "hello world" of data
engineering: **fetch → inspect → transform → save**.

---

## What This Project Does

1. **Fetches** user records from a free test API (`jsonplaceholder.typicode.com`).
2. **Describes** the structure of the data (so you can see what you're working with).
3. **Extracts** key fields and builds simple Python structures (lists, tuples, dicts).
4. **Flattens** nested records into single-level rows.
5. **Exports** everything to `output/customers_clean.csv`.

No API key, no sign-up — just run it.

---

## Requirements

- Python 3.9+
- `requests`
- `pandas`

Install the dependencies:

```bash
pip install requests 
pip install pandas
```
```
Top-level container: list (length: 10)

First record: dict
id           -> int  (value: 1)
name         -> str  (value: 'Leanne Graham')
...

Fetched 10 users
First 3 names: ['Leanne Graham', 'Ervin Howell', 'Clementine Bauch']
DataFrame shape: (10, 15)
CSV written to: /path/to/project/output/customers_clean.csv```

# The Pipeline, Step by Step
```
| Step | Function | What It Does |
|:----:|:---------|:-------------|
| 1 | `fetch_users()` | Calls the API, checks the status code, and returns JSON as Python data. |
| 2 | `describe_structure()` | Prints the types of the payload and each field (great for learning). |
| 3 | `extract_core_fields()` | Keeps only `id`, `name`, `email`, `city`, `company`. |
| 4 | `build_structures()` | Builds a list of names, a list of `(id, email)` tuples, and an `id → city` dict. |
| 5 | `flatten_user()` | Turns nested dicts like `address.geo.lat` into flat keys like `address_geo_lat`. |
| 6 | `to_dataframe()` | Converts the flat records into a Pandas DataFrame with a fixed column order. |
| 7 | `export_csv()` | Writes the DataFrame to CSV, creating the `output/` folder if needed. |```


# Error Handling in `fetch_users()`

`fetch_users()` **fails loudly and clearly** when things go wrong. This is the pattern to copy in any real API client.

## The Three Failure Modes

| Failure | What Happens | Why It Matters |
|:--------|:-------------|:---------------|
| **Connection error / timeout** | Raises `RuntimeError` with the URL. | Network problems are surfaced immediately. |
| **Non-200 status** | Raises `HTTPError`. | A `404` or `500` is never silently ignored. |
| **Invalid JSON** | Raises `ValueError`. | A malformed body is caught at the boundary. |

### Output
After exporting the data to csv it will have 15 columns and 10 rows


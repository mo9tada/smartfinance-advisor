"""Bronze layer: extract raw dataframes, then ingest raw tables."""

import os
import pandas as pd
import requests
import datetime
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import get_database_connection, close_database_connection
from config import API_BASE_URL, API_INTERVAL, API_START_DATE
from config import TIINGO_API_KEY, TIINGO_BASE_URL, TIINGO_START_DATE
from utils import labels, stooq_label_map

def _ensure_data_dir(path: str = "data") -> str:
    """Create the local data folder if needed."""
    os.makedirs(path, exist_ok=True)
    return path

def _build_stooq_url(stooq_ticker: str, interval: str, start_date: str) -> str:
    # Build the Stooq download URL for one ticker
    # start_date is expected in YYYYMMDD
    d2 = datetime.date.today().strftime("%Y%m%d")  # today's date in YYYYMMDD
    return f"{API_BASE_URL}?s={stooq_ticker}&i={interval}&d1={start_date}&d2={d2}"

def _download_stooq_csv_to_file(label: str, interval: str = API_INTERVAL, out_dir: str = "data") -> str | None:
    """
    Download Stooq CSV for one ticker and save locally.
    Returns the local filepath, or None on failure.
    """
    _ensure_data_dir(out_dir)
    stooq_ticker = stooq_label_map.get(label, label.lower())
    url = _build_stooq_url(stooq_ticker=stooq_ticker, interval=interval, start_date=API_START_DATE)
    out_path = os.path.join(out_dir, f"{label}.csv")

    try:
        # Download the CSV file
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            print(f"CSV {label}: HTTP {r.status_code}")
            return None
        with open(out_path, "wb") as f:
            f.write(r.content)
        return out_path
    except Exception as e:
        print(f"CSV {label}: download error ({e})")
        return None

def extract_csv_to_dataframe():
    """
    Extract raw data by downloading Stooq CSV files, then loading them into a dataframe.
    (Download -> CSV file -> dataframe)
    """
    print("Extracting CSV (stooq download)...")
    try:
        frames = []
        ingestion_ts = str(datetime.datetime.now())

        def _extract_one_csv(label: str):
            local_path = _download_stooq_csv_to_file(label=label, interval=API_INTERVAL, out_dir="data")

            # Fallback: if user already uploaded a file, use it
            if local_path is None:
                candidate = os.path.join("data", f"{label}.csv")
                if os.path.exists(candidate):
                    local_path = candidate
                    print(f"CSV {label}: using existing file")
                else:
                    return None

            try:
                df = pd.read_csv(local_path, dtype=str)
            except Exception as e:
                print(f"CSV {label}: parsing error ({e})")
                return None

            if df is None or len(df) == 0:
                print(f"CSV {label}: empty")
                return None

            df["ticker"] = label
            df["ingestion_timestamp"] = ingestion_ts
            df["source_name"] = "STOOQ_CSV"
            df["source_file"] = local_path
            print(f"CSV {label}: {len(df)} rows")
            return df

        max_workers = min(8, max(1, len(labels)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_extract_one_csv, label) for label in labels]
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    frames.append(result)

        if not frames:
            return None

        combined = pd.concat(frames, ignore_index=True)
        print(f"CSV total: {len(combined)} rows")
        return combined
    except Exception as e:
        print(f"Error extracting CSV: {e}")
        return None

def extract_api_to_dataframe():
    """Extract raw API data from Tiingo (all tickers) to a dataframe."""
    print("Extracting API (tiingo)...")
    try:
        if not TIINGO_API_KEY:
            print("API error: missing TIINGO_API_KEY")
            return None

        frames = []
        ingestion_ts = str(datetime.datetime.now())
        end_date = datetime.date.today().isoformat()

        def _extract_one_api(label: str):
            try:
                api_url = f"{TIINGO_BASE_URL}/{label.lower()}/prices?startDate={TIINGO_START_DATE}&endDate={end_date}"
                response = requests.get(
                    api_url,
                    headers={"Authorization": f"Token {TIINGO_API_KEY}"},
                    timeout=60,
                )
            except Exception as req_err:
                print(f"API {label}: request error ({req_err})")
                return None

            if response.status_code != 200:
                print(f"API {label}: HTTP {response.status_code}")
                return None

            data = response.json()
            if not data:
                print(f"API {label}: empty")
                return None

            # Keep the raw API data as-is, no normalization or column renaming
            df = pd.DataFrame(data)
            # Add only minimal metadata columns
            df["ticker"] = label
            df["ingestion_timestamp"] = ingestion_ts
            df["source_name"] = "TIINGO_API"
            df["source_file"] = api_url

            print(f"API {label}: {len(df)} rows")
            return df

        max_workers = min(8, max(1, len(labels)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_extract_one_api, label) for label in labels]
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    frames.append(result)

        if not frames:
            return None

        combined = pd.concat(frames, ignore_index=True)
        print(f"API total: {len(combined)} rows")
        return combined
    except Exception as e:
        print(f"Error extracting API: {e}")
        return None

def ingest_dataframe_to_bronze(df, table_name):
    """Write a raw dataframe to a bronze table (all columns TEXT)."""
    if df is None or len(df) == 0:
        print(f"Skipping ingestion to {table_name}: empty dataframe")
        return False
    
    print(f"Ingesting to {table_name}...")
    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Create table if needed, then add any newly-seen columns.
        columns = ", ".join([f'"{col}" TEXT' for col in df.columns])
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})")

        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            """,
            tuple(table_name.split(".", 1)),
        )
        existing_cols = {row[0] for row in cursor.fetchall()}

        for col in df.columns:
            if col not in existing_cols:
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN "{col}" TEXT')

        # Build conflict keys for upsert.
        date_col = "date" if "date" in df.columns else "Date" if "Date" in df.columns else None
        if date_col and "ticker" in df.columns and "source_name" in df.columns:
            key_cols = ["ticker", "source_name", date_col]
        elif "ticker" in df.columns and "source_name" in df.columns and "ingestion_timestamp" in df.columns:
            key_cols = ["ticker", "source_name", "ingestion_timestamp"]
        else:
            key_cols = list(df.columns)

        idx_name = f"idx_{table_name.replace('.', '_')}_upsert"
        key_cols_sql = ", ".join([f'"{c}"' for c in key_cols])
        cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({key_cols_sql})")

        # COPY into staging table, then upsert into target.
        temp_table = "tmp_bronze_ingest"
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        staging_cols = ", ".join([f'"{col}" TEXT' for col in df.columns])
        cursor.execute(f"CREATE TEMP TABLE {temp_table} ({staging_cols}) ON COMMIT DROP")

        cols = ", ".join([f'"{col}"' for col in df.columns])
        copy_sql = f"COPY {temp_table} ({cols}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"

        copy_df = df.astype(object).where(pd.notna(df), None)
        buffer = io.StringIO()
        copy_df.to_csv(buffer, index=False, header=False, na_rep="\\N")
        buffer.seek(0)
        cursor.copy_expert(copy_sql, buffer)

        non_key_cols = [c for c in df.columns if c not in key_cols]
        if non_key_cols:
            set_sql = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in non_key_cols])
            upsert_sql = (
                f"INSERT INTO {table_name} ({cols}) "
                f"SELECT {cols} FROM {temp_table} "
                f"ON CONFLICT ({key_cols_sql}) DO UPDATE SET {set_sql}"
            )
        else:
            upsert_sql = (
                f"INSERT INTO {table_name} ({cols}) "
                f"SELECT {cols} FROM {temp_table} "
                f"ON CONFLICT ({key_cols_sql}) DO NOTHING"
            )
        cursor.execute(upsert_sql)
        
        conn.commit()
        cursor.close()
        close_database_connection(conn)
        
        print(f"Ingested {len(df)} rows to {table_name}")
        return True
    except Exception as e:
        print(f"Error ingesting to {table_name}: {e}")
        return False

def ingest_csv_to_bronze():
    """Extract CSV and ingest to bronze"""
    df = extract_csv_to_dataframe()
    if df is not None:
        ingest_dataframe_to_bronze(df, "bronze.ohlcv_csv_raw")
    return df

def ingest_api_to_bronze():
    """Extract API and ingest to bronze"""
    df = extract_api_to_dataframe()
    if df is not None:
        ingest_dataframe_to_bronze(df, "bronze.ohlcv_api_raw")
    return df

"""Silver layer: clean/standardize bronze dataframes, then load to DB."""

import pandas as pd
import io
from config import get_database_connection, close_database_connection
from utils import SILVER_COLUMN_LABELS

def transform_bronze_to_silver(bronze_csv_df, bronze_api_df):
    """Transform bronze dataframes to silver dataframe"""
    print("Transforming bronze to silver...")
    
    try:
        # Merge raw sources
        frames_to_concat = []
        if bronze_csv_df is not None and not bronze_csv_df.empty:
            frames_to_concat.append(bronze_csv_df)
        if bronze_api_df is not None and not bronze_api_df.empty:
            frames_to_concat.append(bronze_api_df)
            
        if not frames_to_concat:
            return None
            
        # Standardize column names for both Stooq CSV and Tiingo API
        # Stooq CSV columns: Date, Open, High, Low, Close, Volume
        # Tiingo API columns: date, open, high, low, close, volume
        column_mapping = {
            "Date": "date",
            "Open": "open_price",
            "High": "high_price",
            "Low": "low_price",
            "Close": "close_price",
            "Volume": "volume",
            "date": "date",
            "open": "open_price",
            "high": "high_price",
            "low": "low_price",
            "close": "close_price",
            "volume": "volume",
        }
        # Rename each source BEFORE merging. Renaming after the concat produced
        # two "date" columns (from "Date" and "date"); keeping the first one
        # wiped the dates of every API row, which were then dropped.
        frames_to_concat = [
            frame.rename(columns=column_mapping).loc[:, lambda f: ~f.columns.duplicated()]
            for frame in frames_to_concat
        ]
        merged_df = pd.concat(frames_to_concat, ignore_index=True)
        print(f"Merged: {len(merged_df)} rows")

        # Keep only the silver columns we support (add missing columns as NaN)
        for col in SILVER_COLUMN_LABELS:
            if col not in merged_df.columns:
                merged_df[col] = pd.NA
        merged_df = merged_df[SILVER_COLUMN_LABELS]

        # Convert types
        merged_df["date"] = pd.to_datetime(merged_df["date"], errors="coerce")
        merged_df["ingestion_timestamp"] = pd.to_datetime(merged_df["ingestion_timestamp"], errors="coerce").dt.strftime("%Y-%m-%d")
        merged_df["open_price"] = pd.to_numeric(merged_df["open_price"], errors="coerce")
        merged_df["high_price"] = pd.to_numeric(merged_df["high_price"], errors="coerce")
        merged_df["low_price"] = pd.to_numeric(merged_df["low_price"], errors="coerce")
        merged_df["close_price"] = pd.to_numeric(merged_df["close_price"], errors="coerce")
        merged_df["volume"] = pd.to_numeric(merged_df["volume"], errors="coerce").round().astype("Int64")

        # Basic cleaning rules
        rows_before = len(merged_df)
        # Deduplicate on business keys (ignore ingestion timestamp/source)
        dedupe_cols = [c for c in ["ticker", "date", "open_price", "high_price", "low_price", "close_price", "volume"] if c in merged_df.columns]
        merged_df = merged_df.drop_duplicates(subset=dedupe_cols if dedupe_cols else None)
        merged_df = merged_df.dropna(subset=["close_price", "open_price", "high_price", "low_price", "date"])
        merged_df = merged_df[merged_df["high_price"] >= merged_df["low_price"]]
        merged_df = merged_df[merged_df["volume"] >= 0]
        # Sort by ticker+date to keep each time series ordered
        sort_cols = ["date"]
        if "ticker" in merged_df.columns:
            sort_cols = ["ticker", "date"]
        merged_df = merged_df.sort_values(by=sort_cols, ascending=True).reset_index(drop=True)

        rows_after = len(merged_df)
        print(f"Cleaned: {rows_before} -> {rows_after} rows")

        return merged_df
    except Exception as e:
        print(f"Error transforming to silver: {e}")
        return None

def load_silver_to_db(silver_df):
    """Load the silver dataframe into Postgres."""
    if silver_df is None or len(silver_df) == 0:
        print("Skipping silver load: empty dataframe")
        return False
    
    print("Loading silver to database...")
    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE silver.ohlcv_cleaned (
                ticker               TEXT,
                date                 DATE,
                open_price           FLOAT,
                high_price           FLOAT,
                low_price            FLOAT,
                close_price          FLOAT,
                volume               BIGINT,
                ingestion_timestamp  DATE,
                source_name          TEXT,
                CONSTRAINT ohlcv_cleaned_pk PRIMARY KEY (ticker, date)
            )
        """)

        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_silver_ohlcv_cleaned_key ON silver.ohlcv_cleaned (ticker, date)"
        )
        
        copy_sql = """
            COPY silver.ohlcv_cleaned
            (ticker, date, open_price, high_price, low_price, close_price, volume, ingestion_timestamp, source_name)
            FROM STDIN WITH (FORMAT CSV, NULL '\\N')
        """

        copy_df = pd.DataFrame({
            "ticker": silver_df["ticker"].where(pd.notna(silver_df["ticker"]), None),
            "date": silver_df["date"],
            "open_price": silver_df["open_price"],
            "high_price": silver_df["high_price"],
            "low_price": silver_df["low_price"],
            "close_price": silver_df["close_price"],
            "volume": silver_df["volume"].where(pd.notna(silver_df["volume"]), None),
            "ingestion_timestamp": pd.to_datetime(silver_df["ingestion_timestamp"], errors="coerce").dt.date,
            "source_name": silver_df["source_name"].where(pd.notna(silver_df["source_name"]), None),
        })

        temp_table = "tmp_silver_ingest"
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.execute(
            f"""
            CREATE TEMP TABLE {temp_table} (
                ticker               TEXT,
                date                 DATE,
                open_price           FLOAT,
                high_price           FLOAT,
                low_price            FLOAT,
                close_price          FLOAT,
                volume               BIGINT,
                ingestion_timestamp  DATE,
                source_name          TEXT
            ) ON COMMIT DROP
            """
        )

        buffer = io.StringIO()
        copy_df.to_csv(buffer, index=False, header=False, na_rep="\\N")
        buffer.seek(0)

        cursor.copy_expert(
            copy_sql.replace("silver.ohlcv_cleaned", temp_table),
            buffer,
        )

        cursor.execute(
            f"""
            INSERT INTO silver.ohlcv_cleaned
            (ticker, date, open_price, high_price, low_price, close_price, volume, ingestion_timestamp, source_name)
            SELECT ticker, date, open_price, high_price, low_price, close_price, volume, ingestion_timestamp, source_name
            FROM {temp_table}
            ON CONFLICT (ticker, date) DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                ingestion_timestamp = EXCLUDED.ingestion_timestamp,
                source_name = EXCLUDED.source_name
            """
        )
        
        conn.commit()
        cursor.close()
        close_database_connection(conn)
        
        print(f"Loaded {len(silver_df)} rows to silver")
        return True
    except Exception as e:
        print(f"Error loading silver: {e}")
        return False

def transform_and_clean_to_silver(bronze_csv_df, bronze_api_df):
    """Transform bronze dataframes and load to silver"""
    silver_df = transform_bronze_to_silver(bronze_csv_df, bronze_api_df)
    if silver_df is not None:
        load_silver_to_db(silver_df)
    return silver_df

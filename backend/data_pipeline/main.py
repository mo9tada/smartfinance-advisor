"""Main pipeline runner (Bronze → Silver → Gold)."""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path so medallion layers and main can find config/utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_database_connection, close_database_connection
from medallion.bronze_layer import extract_csv_to_dataframe, extract_api_to_dataframe, ingest_dataframe_to_bronze
from medallion.silver_layer import transform_and_clean_to_silver
from medallion.gold_layer import calculate_kpis_to_gold

def get_table_row_count(table_name):
    """Get row count from a DB table."""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        close_database_connection(conn)
        return count
    except Exception as e:
        print(f"Error counting {table_name}: {e}")
        return 0

def delete_all_csvs_in_data_dir(data_dir: str = "data") -> int:
    """Delete all `*.csv` in `data_dir` (local files)."""
    deleted = 0
    data_path = Path(data_dir)
    if not data_path.exists():
        return 0

    for csv_path in data_path.glob("*.csv"):
        try:
            csv_path.unlink()
            deleted += 1
        except Exception as e:
            print(f"Cleanup error deleting {csv_path}: {e}")
    return deleted

def run_full_pipeline():
    """Run the full pipeline and load results into Postgres."""
    print("=" * 50)
    print("PIPELINE START")
    print("=" * 50)
    
    # BRONZE: extract raw dataframes, then write to bronze tables
    print("\n[BRONZE] Extracting...")
    try:
        bronze_csv_df = extract_csv_to_dataframe()
        bronze_api_df = extract_api_to_dataframe()
        
        if bronze_csv_df is not None:
            ingest_dataframe_to_bronze(bronze_csv_df, "bronze.ohlcv_csv_raw")
        if bronze_api_df is not None:
            ingest_dataframe_to_bronze(bronze_api_df, "bronze.ohlcv_api_raw")
        
        print("[BRONZE] Complete")
    except Exception as e:
        print(f"[BRONZE] Error: {e}")
        return
    
    # SILVER: clean/standardize, then write to silver table
    print("\n[SILVER] Transforming...")
    try:
        if bronze_csv_df is None and bronze_api_df is None:
            print("[SILVER] Missing both bronze dataframes")
            return
        
        silver_df = transform_and_clean_to_silver(bronze_csv_df, bronze_api_df)
        print("[SILVER] Complete")
    except Exception as e:
        print(f"[SILVER] Error: {e}")
        return
    
    # GOLD: compute KPIs, then write to gold table
    print("\n[GOLD] Calculating KPIs...")
    try:
        if silver_df is None:
            print("[GOLD] Missing silver dataframe")
            return
        
        gold_df = calculate_kpis_to_gold(silver_df)
        print("[GOLD] Complete")
    except Exception as e:
        print(f"[GOLD] Error: {e}")
        return
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Bronze CSV: {get_table_row_count('bronze.ohlcv_csv_raw')} rows")
    print(f"Bronze API: {get_table_row_count('bronze.ohlcv_api_raw')} rows")
    print(f"Silver: {get_table_row_count('silver.ohlcv_cleaned')} rows")
    print(f"Gold: {get_table_row_count('gold.ohlcv_kpis')} rows")
    
    # Cleanup: delete downloaded/uploaded CSVs
    print("\n[Cleanup] Deleting data/*.csv ...")
    try:
        deleted = delete_all_csvs_in_data_dir("data")
        print(f"Deleted {deleted} file(s)")
    except Exception as e:
        print(f"Cleanup error: {e}")
    
    
    print("\n" + "=" * 50)
    print("PIPELINE COMPLETE")
    print("=" * 50)



if __name__ == "__main__":
    run_full_pipeline()

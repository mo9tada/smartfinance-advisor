"""Law ingestion pipeline runner (Bronze -> Silver -> Gold)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

data_pipeline_root = Path(__file__).resolve().parents[1]
backend_root = data_pipeline_root.parent
sys.path.insert(0, str(data_pipeline_root))
sys.path.insert(0, str(backend_root))

from law_pipeline.bronze_layer import (
    extract_pdfs_to_dataframe,
    ingest_dataframe_to_bronze,
    truncate_bronze_table,
)
from law_pipeline.silver_layer import transform_and_clean_to_silver, truncate_silver_table
from law_pipeline.gold_layer import calculate_law_gold, truncate_gold_table


def _law_data_dir() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    repo_root = backend_root.parent
    return repo_root / "data" / "law" / "law"


def run_law_pipeline(reset: bool = True) -> None:
    print("=" * 60)
    print("LAW PIPELINE START")
    print("=" * 60)

    if reset:
        print("[RESET] Clearing existing law tables...")
        truncate_bronze_table()
        truncate_silver_table()
        truncate_gold_table()

    print("\n[BRONZE] Extracting PDFs...")
    bronze_df = extract_pdfs_to_dataframe(_law_data_dir())
    if bronze_df is None:
        print("[BRONZE] No data extracted.")
        return
    ingest_dataframe_to_bronze(bronze_df)
    print("[BRONZE] Complete")

    print("\n[SILVER] Cleaning + chunking...")
    silver_df = transform_and_clean_to_silver(bronze_df)
    if silver_df is None:
        print("[SILVER] No data after cleaning.")
        return
    print("[SILVER] Complete")

    print("\n[GOLD] Finalizing + updating RAG...")
    gold_df = calculate_law_gold(silver_df, reset_rag=reset)
    if gold_df is None:
        print("[GOLD] No gold output.")
        return
    print("[GOLD] Complete")

    print("\n" + "=" * 60)
    print("LAW PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_law_pipeline(reset=True)

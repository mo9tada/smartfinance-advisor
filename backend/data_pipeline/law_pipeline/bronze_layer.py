"""Bronze layer for law ingestion: extract raw PDF text and store pages."""

from __future__ import annotations

import datetime
import hashlib
import io
from pathlib import Path
from typing import List

import pandas as pd
import pdfplumber

from config import get_database_connection, close_database_connection


LAW_BRONZE_SCHEMA = "law_bronze"
LAW_BRONZE_TABLE = f"{LAW_BRONZE_SCHEMA}.law_pages"


def _list_pdf_files(root_dir: Path) -> List[Path]:
    return sorted([p for p in root_dir.rglob("*.pdf") if p.is_file()])


def _file_hash(file_path: Path) -> str:
    hasher = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_pdfs_to_dataframe(pdf_root: Path) -> pd.DataFrame | None:
    """Extract text from all PDFs under pdf_root and return a dataframe."""
    if not pdf_root.exists():
        print(f"PDF directory not found: {pdf_root}")
        return None

    pdf_files = _list_pdf_files(pdf_root)
    if not pdf_files:
        print("No PDF files found for law ingestion.")
        return None

    rows = []
    ingestion_ts = datetime.datetime.utcnow().isoformat()

    for pdf_path in pdf_files:
        try:
            file_hash = _file_hash(pdf_path)
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_index, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    rows.append({
                        "doc_name": pdf_path.name,
                        "page_number": page_index,
                        "text": text,
                        "ingestion_timestamp": ingestion_ts,
                        "source_file": str(pdf_path),
                        "source_hash": file_hash,
                    })
        except Exception as e:
            print(f"PDF read error ({pdf_path}): {e}")

    if not rows:
        return None

    return pd.DataFrame(rows)


def _ensure_schema(cursor):
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {LAW_BRONZE_SCHEMA}")


def truncate_bronze_table():
    """Clear bronze table for re-ingest."""
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        _ensure_schema(cursor)
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {LAW_BRONZE_TABLE} ("
            "doc_name TEXT,"
            "page_number INTEGER,"
            "text TEXT,"
            "ingestion_timestamp TEXT,"
            "source_file TEXT,"
            "source_hash TEXT"
            ")"
        )
        cursor.execute(f"TRUNCATE TABLE {LAW_BRONZE_TABLE}")
        conn.commit()
    finally:
        cursor.close()
        close_database_connection(conn)


def ingest_dataframe_to_bronze(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        print("Skipping bronze ingestion: empty dataframe")
        return False

    print(f"Ingesting {len(df)} rows to {LAW_BRONZE_TABLE}...")
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        _ensure_schema(cursor)
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {LAW_BRONZE_TABLE} ("
            "doc_name TEXT,"
            "page_number INTEGER,"
            "text TEXT,"
            "ingestion_timestamp TEXT,"
            "source_file TEXT,"
            "source_hash TEXT,"
            "CONSTRAINT law_pages_pk PRIMARY KEY (doc_name, page_number)"
            ")"
        )
        cursor.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS idx_law_pages_pk ON {LAW_BRONZE_TABLE} (doc_name, page_number)"
        )

        temp_table = "tmp_law_bronze"
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.execute(
            f"CREATE TEMP TABLE {temp_table} ("
            "doc_name TEXT,"
            "page_number INTEGER,"
            "text TEXT,"
            "ingestion_timestamp TEXT,"
            "source_file TEXT,"
            "source_hash TEXT"
            ") ON COMMIT DROP"
        )

        copy_df = df[[
            "doc_name",
            "page_number",
            "text",
            "ingestion_timestamp",
            "source_file",
            "source_hash",
        ]].copy()

        buffer = pd.DataFrame(copy_df).to_csv(index=False, header=False, na_rep="\\N")
        cursor.copy_expert(
            f"COPY {temp_table} (doc_name, page_number, text, ingestion_timestamp, source_file, source_hash) FROM STDIN WITH (FORMAT CSV, NULL '\\N')",
            io.StringIO(buffer),
        )

        cursor.execute(
            f"""
            INSERT INTO {LAW_BRONZE_TABLE}
            (doc_name, page_number, text, ingestion_timestamp, source_file, source_hash)
            SELECT doc_name, page_number, text, ingestion_timestamp, source_file, source_hash
            FROM {temp_table}
            ON CONFLICT (doc_name, page_number) DO UPDATE SET
                text = EXCLUDED.text,
                ingestion_timestamp = EXCLUDED.ingestion_timestamp,
                source_file = EXCLUDED.source_file,
                source_hash = EXCLUDED.source_hash
            """
        )

        conn.commit()
        print("Bronze ingestion complete.")
        return True
    except Exception as e:
        print(f"Bronze ingestion error: {e}")
        return False
    finally:
        cursor.close()
        close_database_connection(conn)

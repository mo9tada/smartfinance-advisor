"""Silver layer for law ingestion: clean text and chunk pages."""

from __future__ import annotations

import io
import re
from typing import List

import pandas as pd

from config import get_database_connection, close_database_connection


LAW_SILVER_SCHEMA = "law_silver"
LAW_SILVER_TABLE = f"{LAW_SILVER_SCHEMA}.law_chunks"


_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def _clean_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    return cleaned


def _detect_language(text: str) -> str:
    if _ARABIC_RE.search(text):
        return "ar"
    return "fr"


def _chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == length:
            break
        start = max(0, end - overlap)
    return chunks


def transform_bronze_to_silver(bronze_df: pd.DataFrame) -> pd.DataFrame | None:
    if bronze_df is None or bronze_df.empty:
        return None

    rows = []
    for _, row in bronze_df.iterrows():
        text = _clean_text(row.get("text", ""))
        if not text:
            continue

        chunks = _chunk_text(text)
        for idx, chunk in enumerate(chunks):
            rows.append({
                "doc_name": row.get("doc_name"),
                "page_number": row.get("page_number"),
                "chunk_index": idx,
                "text": chunk,
                "language": _detect_language(chunk),
                "ingestion_timestamp": row.get("ingestion_timestamp"),
                "source_file": row.get("source_file"),
                "source_hash": row.get("source_hash"),
            })

    if not rows:
        return None

    return pd.DataFrame(rows)


def _ensure_schema(cursor):
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {LAW_SILVER_SCHEMA}")


def truncate_silver_table():
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        _ensure_schema(cursor)
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {LAW_SILVER_TABLE} ("
            "doc_name TEXT,"
            "page_number INTEGER,"
            "chunk_index INTEGER,"
            "text TEXT,"
            "language TEXT,"
            "ingestion_timestamp TEXT,"
            "source_file TEXT,"
            "source_hash TEXT"
            ")"
        )
        cursor.execute(f"TRUNCATE TABLE {LAW_SILVER_TABLE}")
        conn.commit()
    finally:
        cursor.close()
        close_database_connection(conn)


def load_silver_to_db(silver_df: pd.DataFrame) -> bool:
    if silver_df is None or silver_df.empty:
        print("Skipping silver load: empty dataframe")
        return False

    print(f"Loading {len(silver_df)} rows to {LAW_SILVER_TABLE}...")
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        _ensure_schema(cursor)
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {LAW_SILVER_TABLE} ("
            "doc_name TEXT,"
            "page_number INTEGER,"
            "chunk_index INTEGER,"
            "text TEXT,"
            "language TEXT,"
            "ingestion_timestamp TEXT,"
            "source_file TEXT,"
            "source_hash TEXT,"
            "CONSTRAINT law_chunks_pk PRIMARY KEY (doc_name, page_number, chunk_index)"
            ")"
        )
        cursor.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS idx_law_chunks_pk ON {LAW_SILVER_TABLE} (doc_name, page_number, chunk_index)"
        )

        temp_table = "tmp_law_silver"
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.execute(
            f"CREATE TEMP TABLE {temp_table} ("
            "doc_name TEXT,"
            "page_number INTEGER,"
            "chunk_index INTEGER,"
            "text TEXT,"
            "language TEXT,"
            "ingestion_timestamp TEXT,"
            "source_file TEXT,"
            "source_hash TEXT"
            ") ON COMMIT DROP"
        )

        buffer = silver_df[[
            "doc_name",
            "page_number",
            "chunk_index",
            "text",
            "language",
            "ingestion_timestamp",
            "source_file",
            "source_hash",
        ]].to_csv(index=False, header=False, na_rep="\\N")

        cursor.copy_expert(
            f"COPY {temp_table} (doc_name, page_number, chunk_index, text, language, ingestion_timestamp, source_file, source_hash) FROM STDIN WITH (FORMAT CSV, NULL '\\N')",
            io.StringIO(buffer),
        )

        cursor.execute(
            f"""
            INSERT INTO {LAW_SILVER_TABLE}
            (doc_name, page_number, chunk_index, text, language, ingestion_timestamp, source_file, source_hash)
            SELECT doc_name, page_number, chunk_index, text, language, ingestion_timestamp, source_file, source_hash
            FROM {temp_table}
            ON CONFLICT (doc_name, page_number, chunk_index) DO UPDATE SET
                text = EXCLUDED.text,
                language = EXCLUDED.language,
                ingestion_timestamp = EXCLUDED.ingestion_timestamp,
                source_file = EXCLUDED.source_file,
                source_hash = EXCLUDED.source_hash
            """
        )

        conn.commit()
        print("Silver load complete.")
        return True
    except Exception as e:
        print(f"Silver load error: {e}")
        return False
    finally:
        cursor.close()
        close_database_connection(conn)


def transform_and_clean_to_silver(bronze_df: pd.DataFrame) -> pd.DataFrame | None:
    silver_df = transform_bronze_to_silver(bronze_df)
    if silver_df is not None:
        load_silver_to_db(silver_df)
    return silver_df

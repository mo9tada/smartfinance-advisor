"""Gold layer for law ingestion: prepare final law chunks and update RAG."""

from __future__ import annotations

import hashlib
import io

import pandas as pd

from config import get_database_connection, close_database_connection
from api.services.rag_service import rag_service


LAW_GOLD_SCHEMA = "law_gold"
LAW_GOLD_TABLE = f"{LAW_GOLD_SCHEMA}.law_documents"


def _chunk_id(doc_name: str, page_number: int, chunk_index: int) -> str:
    raw = f"{doc_name}:{page_number}:{chunk_index}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def transform_silver_to_gold(silver_df: pd.DataFrame) -> pd.DataFrame | None:
    if silver_df is None or silver_df.empty:
        return None

    gold_df = silver_df.copy()
    gold_df["chunk_id"] = gold_df.apply(
        lambda r: _chunk_id(str(r["doc_name"]), int(r["page_number"]), int(r["chunk_index"])),
        axis=1,
    )

    gold_df = gold_df.drop_duplicates(subset=["chunk_id"]).reset_index(drop=True)
    return gold_df


def _ensure_schema(cursor):
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {LAW_GOLD_SCHEMA}")


def truncate_gold_table():
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        _ensure_schema(cursor)
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {LAW_GOLD_TABLE} ("
            "chunk_id TEXT PRIMARY KEY,"
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
        cursor.execute(f"TRUNCATE TABLE {LAW_GOLD_TABLE}")
        conn.commit()
    finally:
        cursor.close()
        close_database_connection(conn)


def load_gold_to_db(gold_df: pd.DataFrame) -> bool:
    if gold_df is None or gold_df.empty:
        print("Skipping gold load: empty dataframe")
        return False

    print(f"Loading {len(gold_df)} rows to {LAW_GOLD_TABLE}...")
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        _ensure_schema(cursor)
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {LAW_GOLD_TABLE} ("
            "chunk_id TEXT PRIMARY KEY,"
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
        cursor.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS idx_law_documents_doc_chunk ON {LAW_GOLD_TABLE} (doc_name, page_number, chunk_index)"
        )

        temp_table = "tmp_law_gold"
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.execute(
            f"CREATE TEMP TABLE {temp_table} ("
            "chunk_id TEXT,"
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

        buffer = gold_df[[
            "chunk_id",
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
            f"COPY {temp_table} (chunk_id, doc_name, page_number, chunk_index, text, language, ingestion_timestamp, source_file, source_hash) FROM STDIN WITH (FORMAT CSV, NULL '\\N')",
            io.StringIO(buffer),
        )

        cursor.execute(
            f"""
            INSERT INTO {LAW_GOLD_TABLE}
            (chunk_id, doc_name, page_number, chunk_index, text, language, ingestion_timestamp, source_file, source_hash)
            SELECT chunk_id, doc_name, page_number, chunk_index, text, language, ingestion_timestamp, source_file, source_hash
            FROM {temp_table}
            ON CONFLICT (chunk_id) DO UPDATE SET
                text = EXCLUDED.text,
                language = EXCLUDED.language,
                ingestion_timestamp = EXCLUDED.ingestion_timestamp,
                source_file = EXCLUDED.source_file,
                source_hash = EXCLUDED.source_hash
            """
        )

        conn.commit()
        print("Gold load complete.")
        return True
    except Exception as e:
        print(f"Gold load error: {e}")
        return False
    finally:
        cursor.close()
        close_database_connection(conn)


def update_rag_from_gold(gold_df: pd.DataFrame, reset_collection: bool = False) -> None:
    if gold_df is None or gold_df.empty:
        print("Skipping RAG update: empty dataframe")
        return

    if reset_collection:
        rag_service.reset_finance_collection()

    documents = gold_df["text"].tolist()
    metadatas = []
    ids = []
    for _, row in gold_df.iterrows():
        ids.append(row["chunk_id"])
        metadatas.append({
            "source": row.get("doc_name"),
            "doc_name": row.get("doc_name"),
            "page_number": row.get("page_number"),
            "chunk_index": row.get("chunk_index"),
            "language": row.get("language"),
        })

    rag_service.add_documents(documents=documents, metadatas=metadatas, ids=ids)


def calculate_law_gold(silver_df: pd.DataFrame, reset_rag: bool = False) -> pd.DataFrame | None:
    gold_df = transform_silver_to_gold(silver_df)
    if gold_df is not None:
        load_gold_to_db(gold_df)
        update_rag_from_gold(gold_df, reset_collection=reset_rag)
    return gold_df

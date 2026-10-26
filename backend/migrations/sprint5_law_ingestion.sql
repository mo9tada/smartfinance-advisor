-- Sprint 5: Law ingestion schemas and tables

CREATE SCHEMA IF NOT EXISTS law_bronze;
CREATE SCHEMA IF NOT EXISTS law_silver;
CREATE SCHEMA IF NOT EXISTS law_gold;

CREATE TABLE IF NOT EXISTS law_bronze.law_pages (
    doc_name TEXT,
    page_number INTEGER,
    text TEXT,
    ingestion_timestamp TEXT,
    source_file TEXT,
    source_hash TEXT,
    CONSTRAINT law_pages_pk PRIMARY KEY (doc_name, page_number)
);

CREATE TABLE IF NOT EXISTS law_silver.law_chunks (
    doc_name TEXT,
    page_number INTEGER,
    chunk_index INTEGER,
    text TEXT,
    language TEXT,
    ingestion_timestamp TEXT,
    source_file TEXT,
    source_hash TEXT,
    CONSTRAINT law_chunks_pk PRIMARY KEY (doc_name, page_number, chunk_index)
);

CREATE TABLE IF NOT EXISTS law_gold.law_documents (
    chunk_id TEXT PRIMARY KEY,
    doc_name TEXT,
    page_number INTEGER,
    chunk_index INTEGER,
    text TEXT,
    language TEXT,
    ingestion_timestamp TEXT,
    source_file TEXT,
    source_hash TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_law_pages_pk
    ON law_bronze.law_pages (doc_name, page_number);

CREATE UNIQUE INDEX IF NOT EXISTS idx_law_chunks_pk
    ON law_silver.law_chunks (doc_name, page_number, chunk_index);

CREATE UNIQUE INDEX IF NOT EXISTS idx_law_documents_doc_chunk
    ON law_gold.law_documents (doc_name, page_number, chunk_index);

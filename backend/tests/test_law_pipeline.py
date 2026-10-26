"""Unit tests for the legal-document pipeline used by the RAG assistant."""
import pandas as pd

from data_pipeline.law_pipeline.silver_layer import (
  _chunk_text,
  _clean_text,
  _detect_language,
  transform_bronze_to_silver,
)


def test_clean_text_collapses_whitespace():
    assert _clean_text("  Article\n\n 12 \t alinéa ") == "Article 12 alinéa"


def test_detect_language_arabic_and_french():
    assert _detect_language("قانون المالية لسنة 2024") == "ar"
    assert _detect_language("Loi de finances pour l'année 2024") == "fr"


def test_chunks_cover_text_with_overlap():
    text = "".join(str(i % 10) for i in range(4000))
    chunks = _chunk_text(text, chunk_size=1500, overlap=200)
    assert [len(c) for c in chunks] == [1500, 1500, 1400]
    # consecutive chunks share exactly `overlap` characters
    assert chunks[0][-200:] == chunks[1][:200]
    assert chunks[1][-200:] == chunks[2][:200]


def test_short_text_is_a_single_chunk():
    assert _chunk_text("court", chunk_size=1500, overlap=200) == ["court"]
    assert _chunk_text("") == []


def test_transform_bronze_to_silver_builds_indexed_chunks():
    bronze = pd.DataFrame(
        {
            "doc_name": ["LF2025.pdf", "LF2025.pdf"],
            "page_number": [1, 2],
            "text": ["x" * 2000, "   "],  # empty page is skipped
            "ingestion_timestamp": ["2025-01-01"] * 2,
            "source_file": ["data/law/LF2025.pdf"] * 2,
            "source_hash": ["abc"] * 2,
        }
    )
    silver = transform_bronze_to_silver(bronze)
    assert silver["chunk_index"].tolist() == [0, 1]
    assert set(silver["page_number"]) == {1}
    assert set(silver["language"]) == {"fr"}

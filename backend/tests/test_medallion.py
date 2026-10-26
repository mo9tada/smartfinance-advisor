"""Unit tests for the market-data Medallion transforms (no database needed)."""
import pandas as pd
import pytest

from data_pipeline.medallion.gold_layer import transform_silver_to_gold
from data_pipeline.medallion.silver_layer import transform_bronze_to_silver


def bronze_csv():
    """Stooq-style columns (capitalised)."""
    return pd.DataFrame(
        {
            "ticker": ["AAPL", "AAPL", "AAPL", "AAPL"],
            "Date": ["2024-01-03", "2024-01-02", "2024-01-02", "2024-01-04"],
            "Open": [10, 9, 9, 11],
            "High": [11, 10, 10, 9],  # last row: high < low -> invalid
            "Low": [9, 8, 8, 10],
            "Close": [10.5, 9.5, 9.5, 10],
            "Volume": [100, 200, 200, 300],
            "ingestion_timestamp": ["2024-02-01"] * 4,
            "source_name": ["stooq"] * 4,
        }
    )


def bronze_api():
    """Tiingo-style columns (lower case)."""
    return pd.DataFrame(
        {
            "ticker": ["MSFT", "MSFT"],
            "date": ["2024-01-02", "2024-01-03"],
            "open": [300, 310],
            "high": [305, 320],
            "low": [295, 305],
            "close": [302, 315],
            "volume": [1000, -5],  # negative volume -> dropped
            "ingestion_timestamp": ["2024-02-01"] * 2,
            "source_name": ["tiingo"] * 2,
        }
    )


def test_silver_merges_sources_and_standardises_columns():
    silver = transform_bronze_to_silver(bronze_csv(), bronze_api())
    assert {"open_price", "high_price", "low_price", "close_price"} <= set(silver.columns)
    assert set(silver["ticker"]) == {"AAPL", "MSFT"}


def test_silver_cleaning_rules():
    silver = transform_bronze_to_silver(bronze_csv(), bronze_api())
    # duplicate AAPL 2024-01-02 removed, high<low row removed, negative volume removed
    assert len(silver) == 3
    assert (silver["high_price"] >= silver["low_price"]).all()
    assert (silver["volume"] >= 0).all()


def test_silver_is_sorted_by_ticker_then_date():
    silver = transform_bronze_to_silver(bronze_csv(), bronze_api())
    assert list(zip(silver["ticker"], silver["date"].dt.strftime("%m-%d"))) == [
        ("AAPL", "01-02"),
        ("AAPL", "01-03"),
        ("MSFT", "01-02"),
    ]


def test_silver_returns_none_without_input():
    assert transform_bronze_to_silver(None, pd.DataFrame()) is None


def silver_two_tickers():
    return pd.DataFrame(
        {
            "ticker": ["A"] * 4 + ["B"] * 2,
            "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2024-01-01", "2024-02-01"]),
            "open_price": [100, 110, 120, 90, 50, 55],
            "high_price": [105, 115, 125, 95, 52, 60],
            "low_price": [95, 105, 115, 85, 48, 50],
            "close_price": [100, 110, 120, 90, 50, 55],
            "volume": [1, 1, 1, 1, 1, 1],
        }
    )


def test_gold_returns_are_computed_per_ticker():
    gold = transform_silver_to_gold(silver_two_tickers())
    a = gold[gold["ticker"] == "A"]["monthly_return"].tolist()
    b = gold[gold["ticker"] == "B"]["monthly_return"].tolist()
    assert pd.isna(a[0]) and pd.isna(b[0])  # first point of each series has no return
    assert a[1] == pytest.approx(10.0)
    assert b[1] == pytest.approx(10.0)  # not computed against ticker A's last close


def test_gold_drawdown_and_peak():
    gold = transform_silver_to_gold(silver_two_tickers())
    a = gold[gold["ticker"] == "A"]
    assert a["running_peak_close"].tolist() == [100, 110, 120, 120]
    assert a["drawdown"].iloc[-1] == pytest.approx(90 / 120 - 1)


def test_gold_range_percent_and_valid_ohlc():
    gold = transform_silver_to_gold(silver_two_tickers())
    first = gold.iloc[0]
    assert first["range_percent"] == pytest.approx((105 - 95) / 100 * 100)
    assert gold["invalid_ohlc_flag"].sum() == 0

"""Gold layer: compute KPIs from silver, then load to DB."""

import pandas as pd
import io
from config import get_database_connection, close_database_connection
from utils import GOLD_KPI_LABELS

def transform_silver_to_gold(silver_df):
    """Transform silver dataframe to gold with KPIs"""
    print("Transforming silver to gold...")
    
    try:
        gold_df = silver_df.copy()
        # Keep each ticker ordered for rolling windows
        sort_cols = ["date"]
        if "ticker" in gold_df.columns:
            sort_cols = ["ticker", "date"]
        gold_df = gold_df.sort_values(by=sort_cols, ascending=True).reset_index(drop=True)
        
        # KPI calculations
        print("Calculating KPIs...")
        if "ticker" in gold_df.columns:
            # Compute KPIs per ticker (don't mix series)
            g = gold_df.groupby("ticker", group_keys=False)
            gold_df[GOLD_KPI_LABELS[0]] = (
                g["close_price"].rolling(window=12, min_periods=1).mean().reset_index(level=0, drop=True)
            )
            gold_df[GOLD_KPI_LABELS[1]] = (
                g["close_price"].rolling(window=24, min_periods=1).mean().reset_index(level=0, drop=True)
            )
            gold_df[GOLD_KPI_LABELS[2]] = g["close_price"].pct_change() * 100
            gold_df[GOLD_KPI_LABELS[3]] = (
                g[GOLD_KPI_LABELS[2]].rolling(window=12, min_periods=2).std().reset_index(level=0, drop=True)
            )
            gold_df[GOLD_KPI_LABELS[4]] = g["close_price"].cummax()
        else:
            gold_df[GOLD_KPI_LABELS[0]] = gold_df["close_price"].rolling(window=12, min_periods=1).mean()
            gold_df[GOLD_KPI_LABELS[1]] = gold_df["close_price"].rolling(window=24, min_periods=1).mean()
            previous_close = gold_df["close_price"].shift(1)
            gold_df[GOLD_KPI_LABELS[2]] = ((gold_df["close_price"] - previous_close) / previous_close) * 100
            gold_df[GOLD_KPI_LABELS[3]] = gold_df[GOLD_KPI_LABELS[2]].rolling(window=12, min_periods=2).std()
            gold_df[GOLD_KPI_LABELS[4]] = gold_df["close_price"].cummax()

        gold_df[GOLD_KPI_LABELS[5]] = (gold_df["close_price"] / gold_df[GOLD_KPI_LABELS[4]]) - 1
        gold_df[GOLD_KPI_LABELS[6]] = ((gold_df["high_price"] - gold_df["low_price"]) / gold_df["close_price"]) * 100
        
        ohlc_max = gold_df[["open_price", "high_price", "low_price", "close_price"]].max(axis=1)
        gold_df[GOLD_KPI_LABELS[7]] = (gold_df["high_price"] < ohlc_max).astype(int)
        
        invalid_count = gold_df[GOLD_KPI_LABELS[7]].sum()
        print(f"Invalid OHLC rows: {invalid_count}")
        print(f"Transformed {len(gold_df)} rows")
        
        return gold_df
    except Exception as e:
        print(f"Error transforming to gold: {e}")
        return None

def load_gold_to_db(gold_df):
    """Load the gold KPI dataframe into Postgres."""
    if gold_df is None or len(gold_df) == 0:
        print("Skipping gold load: empty dataframe")
        return False
    
    print("Loading gold to database...")
    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE gold.ohlcv_kpis (
                ticker                  TEXT,
                date                    DATE,
                open_price              FLOAT,
                high_price              FLOAT,
                low_price               FLOAT,
                close_price             FLOAT,
                volume                  BIGINT,
                sma_12m                 FLOAT,
                sma_24m                 FLOAT,
                monthly_return          FLOAT,
                rolling_volatility_12m  FLOAT,
                running_peak_close      FLOAT,
                drawdown                FLOAT,
                range_percent           FLOAT,
                invalid_ohlc_flag       INTEGER,
                CONSTRAINT ohlcv_kpis_pk PRIMARY KEY (ticker, date)
            )
        """)

        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_gold_ohlcv_kpis_key ON gold.ohlcv_kpis (ticker, date)"
        )
        
        copy_sql = """
            COPY gold.ohlcv_kpis
            (ticker, date, open_price, high_price, low_price, close_price, volume,
             sma_12m, sma_24m, monthly_return, rolling_volatility_12m,
             running_peak_close, drawdown, range_percent, invalid_ohlc_flag)
            FROM STDIN WITH (FORMAT CSV, NULL '\\N')
        """

        copy_df = pd.DataFrame({
            "ticker": gold_df["ticker"].where(pd.notna(gold_df["ticker"]), None),
            "date": gold_df["date"],
            "open_price": gold_df["open_price"].where(pd.notna(gold_df["open_price"]), None),
            "high_price": gold_df["high_price"].where(pd.notna(gold_df["high_price"]), None),
            "low_price": gold_df["low_price"].where(pd.notna(gold_df["low_price"]), None),
            "close_price": gold_df["close_price"].where(pd.notna(gold_df["close_price"]), None),
            "volume": gold_df["volume"].where(pd.notna(gold_df["volume"]), None),
            "sma_12m": gold_df[GOLD_KPI_LABELS[0]].where(pd.notna(gold_df[GOLD_KPI_LABELS[0]]), None),
            "sma_24m": gold_df[GOLD_KPI_LABELS[1]].where(pd.notna(gold_df[GOLD_KPI_LABELS[1]]), None),
            "monthly_return": gold_df[GOLD_KPI_LABELS[2]].where(pd.notna(gold_df[GOLD_KPI_LABELS[2]]), None),
            "rolling_volatility_12m": gold_df[GOLD_KPI_LABELS[3]].where(pd.notna(gold_df[GOLD_KPI_LABELS[3]]), None),
            "running_peak_close": gold_df[GOLD_KPI_LABELS[4]].where(pd.notna(gold_df[GOLD_KPI_LABELS[4]]), None),
            "drawdown": gold_df[GOLD_KPI_LABELS[5]].where(pd.notna(gold_df[GOLD_KPI_LABELS[5]]), None),
            "range_percent": gold_df[GOLD_KPI_LABELS[6]].where(pd.notna(gold_df[GOLD_KPI_LABELS[6]]), None),
            "invalid_ohlc_flag": gold_df[GOLD_KPI_LABELS[7]].where(pd.notna(gold_df[GOLD_KPI_LABELS[7]]), None),
        })

        temp_table = "tmp_gold_ingest"
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.execute(
            f"""
            CREATE TEMP TABLE {temp_table} (
                ticker                  TEXT,
                date                    DATE,
                open_price              FLOAT,
                high_price              FLOAT,
                low_price               FLOAT,
                close_price             FLOAT,
                volume                  BIGINT,
                sma_12m                 FLOAT,
                sma_24m                 FLOAT,
                monthly_return          FLOAT,
                rolling_volatility_12m  FLOAT,
                running_peak_close      FLOAT,
                drawdown                FLOAT,
                range_percent           FLOAT,
                invalid_ohlc_flag       INTEGER
            ) ON COMMIT DROP
            """
        )

        buffer = io.StringIO()
        copy_df.to_csv(buffer, index=False, header=False, na_rep="\\N")
        buffer.seek(0)

        cursor.copy_expert(
            copy_sql.replace("gold.ohlcv_kpis", temp_table),
            buffer,
        )

        cursor.execute(
            f"""
            INSERT INTO gold.ohlcv_kpis
            (ticker, date, open_price, high_price, low_price, close_price, volume,
             sma_12m, sma_24m, monthly_return, rolling_volatility_12m,
             running_peak_close, drawdown, range_percent, invalid_ohlc_flag)
            SELECT ticker, date, open_price, high_price, low_price, close_price, volume,
                   sma_12m, sma_24m, monthly_return, rolling_volatility_12m,
                   running_peak_close, drawdown, range_percent, invalid_ohlc_flag
            FROM {temp_table}
            ON CONFLICT (ticker, date) DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                sma_12m = EXCLUDED.sma_12m,
                sma_24m = EXCLUDED.sma_24m,
                monthly_return = EXCLUDED.monthly_return,
                rolling_volatility_12m = EXCLUDED.rolling_volatility_12m,
                running_peak_close = EXCLUDED.running_peak_close,
                drawdown = EXCLUDED.drawdown,
                range_percent = EXCLUDED.range_percent,
                invalid_ohlc_flag = EXCLUDED.invalid_ohlc_flag
            """
        )
        
        conn.commit()
        cursor.close()
        close_database_connection(conn)
        
        print(f"Loaded {len(gold_df)} rows to gold")
        return True
    except Exception as e:
        print(f"Error loading gold: {e}")
        return False

def calculate_kpis_to_gold(silver_df):
    """Transform silver dataframe to gold and load to database"""
    gold_df = transform_silver_to_gold(silver_df)
    if gold_df is not None:
        load_gold_to_db(gold_df)
    return gold_df

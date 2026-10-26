# Trading Data Pipeline - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [Installation & Setup](#installation--setup)
5. [Running the Pipeline](#running-the-pipeline)
6. [API Endpoints](#api-endpoints)
7. [Module Reference](#module-reference)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)

---

## Project Overview

This is a **complete financial data pipeline** that follows the **Medallion Architecture** (Bronze → Silver → Gold) pattern for processing OHLCV (Open, High, Low, Close, Volume) financial data.

### Key Features
- **Dual Data Sources**: Ingests data from both CSV files and REST APIs (Stooq)
- **Three-Layer Architecture**: Bronze (raw) → Silver (cleaned) → Gold (KPI-enriched)
- **PostgreSQL Storage**: All data persisted in PostgreSQL with proper schema management
- **REST API**: Flask-based API to query processed data
- **KPI Calculations**: 8 technical indicators computed automatically

### Supported Tickers
- AAPL (Apple)
- MSFT (Microsoft)
- GOOG (Alphabet)
- AMZN (Amazon)
- TSLA (Tesla)
- SPY (S&P 500 ETF)
- JPM (JPMorgan Chase)

---

## Architecture

### Medallion Pattern Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Pipeline Flow                        │
└─────────────────────────────────────────────────────────────┘

CSV File ──┐
           ├──> BRONZE LAYER      ──> SILVER LAYER    ──> GOLD LAYER
API Stooq ─┘    (Raw Data)         (Cleaned Data)      (KPIs)
           
           ┌──────────────────────────────────────────────────┐
           │          PostgreSQL Database                      │
           ├──────────────────────────────────────────────────┤
           │ bronze.ohlcv_csv_raw  │  Raw CSV data           │
           │ bronze.ohlcv_api_raw  │  Raw API data           │
           ├──────────────────────────────────────────────────┤
           │ silver.ohlcv_cleaned  │  Standardized data      │
           ├──────────────────────────────────────────────────┤
           │ gold.ohlcv_kpis       │  KPI-enriched data      │
           └──────────────────────────────────────────────────┘
```

### Layer Descriptions

#### 1. **Bronze Layer** (Raw Data)
- **Purpose**: Store raw, unprocessed data as-is from sources
- **Tables**:
  - `bronze.ohlcv_csv_raw` - Data from CSV files
  - `bronze.ohlcv_api_raw` - Data from REST APIs
- **Column Types**: All `TEXT` (no type conversion)
- **Module**: `bronze_layer.py`

#### 2. **Silver Layer** (Cleaned & Standardized)
- **Purpose**: Transform and standardize data for business use
- **Table**: `silver.ohlcv_cleaned`
- **Transformations Applied**:
  - Data type conversion (TEXT → DATE, FLOAT, BIGINT)
  - Invalid OHLC validation (Open ≤ High ≥ Low, Close within range)
  - Outlier detection
  - Null value handling
  - Date formatting standardization
- **Module**: `silver_layer.py`

#### 3. **Gold Layer** (Business Analytics)
- **Purpose**: Provide KPI-enriched data ready for business intelligence
- **Table**: `gold.ohlcv_kpis`
- **KPIs Calculated**:
  1. **SMA 12M** - 12-month Simple Moving Average
  2. **SMA 24M** - 24-month Simple Moving Average
  3. **Monthly Return** - Month-over-month percentage change
  4. **Rolling Volatility 12M** - 12-month rolling standard deviation
  5. **Running Peak Close** - Cumulative maximum close price
  6. **Drawdown** - Percentage decline from peak: `(Close / Peak) - 1`
  7. **Range Percent** - Daily amplitude: `(High - Low) / Close * 100`
  8. **Invalid OHLC Flag** - Data quality indicator (1 = invalid, 0 = valid)
- **Module**: `gold_layer.py`

---

## Database Schema

### Bronze Schema (Raw Data)

#### `bronze.ohlcv_csv_raw` (CSV Source Data)
```sql
CREATE TABLE bronze.ohlcv_csv_raw (
    ticker              TEXT,      -- Stock ticker symbol (AAPL, MSFT, etc.)
    "Date"              TEXT,      -- Date as text (not converted)
    "Open"              TEXT,      -- Opening price as text
    "High"              TEXT,      -- High price as text
    "Low"               TEXT,      -- Low price as text
    "Close"             TEXT,      -- Closing price as text
    "Volume"            TEXT,      -- Trading volume as text
    ingestion_timestamp TEXT,      -- Timestamp when ingested to DB
    source_name         TEXT,      -- Source identifier ("CSV_FILE")
    source_file         TEXT       -- Original filename
);
```

#### `bronze.ohlcv_api_raw` (API Source Data)
```sql
CREATE TABLE bronze.ohlcv_api_raw (
    ticker              TEXT,      -- Stock ticker symbol
    "Date"              TEXT,      -- Date as text
    "Open"              TEXT,      -- Opening price as text
    "High"              TEXT,      -- High price as text
    "Low"               TEXT,      -- Low price as text
    "Close"             TEXT,      -- Closing price as text
    "Volume"            TEXT,      -- Trading volume as text
    ingestion_timestamp TEXT,      -- Timestamp when ingested to DB
    source_name         TEXT,      -- Source identifier ("REST_API")
    source_file         TEXT       -- Retrieved from Stooq API
);
```

### Silver Schema (Cleaned Data)

#### `silver.ohlcv_cleaned`
```sql
CREATE TABLE silver.ohlcv_cleaned (
    ticker              TEXT,      -- Stock ticker
    date                DATE,      -- Trading date (properly typed)
    open_price          FLOAT,     -- Opening price
    high_price          FLOAT,     -- Highest price
    low_price           FLOAT,     -- Lowest price
    close_price         FLOAT,     -- Closing price
    volume              BIGINT,    -- Trading volume
    ingestion_timestamp TIMESTAMP, -- When data was ingested
    source_name         TEXT       -- Data source ("CSV_FILE" or "REST_API")
);
```

**Data Quality Checks Applied:**
- `open_price <= high_price <= close_price` (basic OHLC validation)
- `low_price <= high_price` (low < high)
- All prices are non-negative
- Volume is non-negative
- Date is valid and not in the future

### Gold Schema (KPI-Enriched Data)

#### `gold.ohlcv_kpis`
```sql
CREATE TABLE gold.ohlcv_kpis (
    ticker                  TEXT,   -- Stock ticker
    date                    DATE,   -- Trading date
    open_price              FLOAT,  -- Opening price
    high_price              FLOAT,  -- Highest price
    low_price               FLOAT,  -- Lowest price
    close_price             FLOAT,  -- Closing price
    volume                  BIGINT, -- Trading volume
    
    -- Technical Indicators (KPIs)
    sma_12m                 FLOAT,  -- 12-month Simple Moving Average
    sma_24m                 FLOAT,  -- 24-month Simple Moving Average
    monthly_return          FLOAT,  -- Monthly percentage return
    rolling_volatility_12m  FLOAT,  -- 12-month rolling standard deviation
    running_peak_close      FLOAT,  -- Cumulative maximum close
    drawdown                FLOAT,  -- Drawdown percentage from peak
    range_percent           FLOAT,  -- Intraday range as % of close
    invalid_ohlc_flag       INTEGER -- Data quality flag (1=invalid, 0=valid)
);
```

**KPI Formulas:**
- `sma_12m = AVG(close_price) over 252 trading days (≈12 months)`
- `sma_24m = AVG(close_price) over 504 trading days (≈24 months)`
- `monthly_return = ((curr_close - prev_month_close) / prev_month_close) * 100`
- `rolling_volatility_12m = STDDEV(daily_returns) over 252 days`
- `running_peak_close = MAX(close_price) up to current date`
- `drawdown = (close_price / running_peak_close) - 1`
- `range_percent = ((high_price - low_price) / close_price) * 100`
- `invalid_ohlc_flag = 1 if any OHLC validation fails, else 0`

---

## Installation & Setup

### 1. Prerequisites

**System Requirements:**
- Python 3.8+
- PostgreSQL 12+ (version 18 recommended)
- Windows/Linux/Mac

**PostgreSQL Installation:**
- Download from: https://www.postgresql.org/download/
- During installation, remember the password for `postgres` user

### 2. Clone/Setup Project

```bash
cd c:\Users\RAGER\Desktop\PFE\DATA\v4
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies Installed:**
- `pandas` - Data manipulation and analysis
- `requests` - HTTP requests for API calls
- `psycopg2-binary` - PostgreSQL adapter for Python
- `python-dotenv` - Load environment variables from `.env`
- `Flask` - Web framework for REST API
- `Flask-CORS` - Enable CORS for cross-origin requests

### 4. Configure Environment Variables

Create/Edit `.env` file:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_pipeline
DB_USER=postgres
DB_PASSWORD=postgres

# API Configuration
TIINGO_API_KEY=your_tiingo_api_key_here
```

**Get Tiingo API Key:**
1. Visit: https://www.tiingo.com/
2. Sign up for free account
3. Copy your API key
4. Add to `.env` file

### 5. Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# In psql console, run:
CREATE DATABASE trading_pipeline;
```

### 6. Setup Database Schema

```bash
# Run setup script
psql -U postgres -d trading_pipeline -f setup_database.sql
```

Or manually copy-paste SQL commands from `setup_database.sql` into your PostgreSQL client.

### 7. Prepare CSV Data (Optional)

Create `data/` directory and add CSV file:

```bash
mkdir data
```

**CSV Format Required:**
```csv
Date,Open,High,Low,Close,Volume
2024-01-01,100.50,102.30,99.80,101.20,1500000
2024-01-02,101.20,103.10,100.90,102.50,1800000
```

---

## Running the Pipeline

### Option 1: Run Complete Pipeline (all 3 layers)

```bash
python main.py
```

**Output:**
```
==================================================
PIPELINE START
==================================================

[BRONZE] Extracting...
[BRONZE] Complete

[SILVER] Transforming...
[SILVER] Complete

[GOLD] Calculating KPIs...
[GOLD] Complete

==================================================
SUMMARY
==================================================
Bronze CSV: 1250 rows
Bronze API: 1250 rows
Silver: 2500 rows
Gold: 2500 rows
```

### Option 2: Run Flask REST API

```bash
python start_api.py
```

**Output:**
```
 Flask API running on http://localhost:5000
 Endpoints available at /api/...
 * Running on http://127.0.0.1:5000
```

---

## API Endpoints

The Flask API provides REST endpoints to query the processed data. All responses are JSON formatted.

### 1. **OHLCV Data Endpoint**

**Route:** `GET /api/ohlcv`

**Description:** Retrieve cleaned OHLCV data from `silver.ohlcv_cleaned`

**Query Parameters:**
| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| `ticker` | string | No | `AAPL` | Filter by stock ticker |
| `start_date` | string | No | `2024-01-01` | Filter from date (YYYY-MM-DD) |
| `end_date` | string | No | `2024-12-31` | Filter to date (YYYY-MM-DD) |
| `limit` | integer | No | `100` | Limit number of rows returned |

**Example Requests:**
```bash
# Get all OHLCV data (limited to 5 rows)
curl "http://localhost:5000/api/ohlcv?limit=5"

# Filter by ticker
curl "http://localhost:5000/api/ohlcv?ticker=AAPL&limit=10"

# Date range filter
curl "http://localhost:5000/api/ohlcv?ticker=MSFT&start_date=2024-01-01&end_date=2024-06-30&limit=50"
```

**Response Example:**
```json
{
  "count": 5,
  "data": [
    {
      "ticker": "AAPL",
      "date": "2024-01-02",
      "open_price": 185.64,
      "high_price": 190.58,
      "low_price": 185.23,
      "close_price": 189.95,
      "volume": 52891500,
      "source_name": "REST_API"
    },
    ...
  ]
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (invalid parameters)
- `500` - Server error

---

### 2. **KPIs Endpoint**

**Route:** `GET /api/kpis`

**Description:** Retrieve KPI-enriched data from `gold.ohlcv_kpis`

**Query Parameters:**
| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| `ticker` | string | No | `AAPL` | Filter by stock ticker |
| `start_date` | string | No | `2024-01-01` | Filter from date |
| `end_date` | string | No | `2024-12-31` | Filter to date |
| `limit` | integer | No | `100` | Limit rows |

**Example Requests:**
```bash
# Get KPIs for all tickers
curl "http://localhost:5000/api/kpis?limit=5"

# Get KPIs for specific ticker
curl "http://localhost:5000/api/kpis?ticker=TSLA&limit=20"

# Filter by date range
curl "http://localhost:5000/api/kpis?ticker=GOOG&start_date=2024-01-01&end_date=2024-03-31"
```

**Response Example:**
```json
{
  "count": 2,
  "data": [
    {
      "ticker": "IBM",
      "date": "1962-01-02",
      "open_price": 3.77187,
      "high_price": 5.0461,
      "low_price": 4.98716,
      "close_price": 4.98716,
      "volume": 593631,
      "sma_12m": 4.98716,
      "sma_24m": 4.98716,
      "monthly_return": null,
      "rolling_volatility_12m": null,
      "running_peak_close": 4.98716,
      "drawdown": 0.0,
      "range_percent": 2.566,
      "invalid_ohlc_flag": 0
    },
    ...
  ]
}
```

---

### 3. **Monthly Returns Endpoint**

**Route:** `GET /api/monthly-returns`

**Description:** Calculate monthly returns (month-over-month percentage change)

**Query Parameters (Required):**
| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| `ticker` | string | **YES** | `AAPL` | Stock ticker (required) |
| `start_date` | string | No | `2024-01-01` | Filter from date |
| `end_date` | string | No | `2024-12-31` | Filter to date |

**Example Requests:**
```bash
# Get monthly returns for AAPL
curl "http://localhost:5000/api/monthly-returns?ticker=AAPL"

# With date filters
curl "http://localhost:5000/api/monthly-returns?ticker=MSFT&start_date=2023-01-01&end_date=2024-12-31"
```

**Response Example:**
```json
{
  "ticker": "AAPL",
  "status": "success",
  "data": [
    {
      "date": "2024-01-31",
      "close_price": 189.95,
      "monthly_return": 8.75
    },
    {
      "date": "2024-02-29",
      "close_price": 192.53,
      "monthly_return": 1.36
    }
  ]
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "ticker parameter is required"
}
```

---

### 4. **Indicators Endpoints**

Additional technical indicator endpoints (see `routes/indicators.py` for full list).

---

## Module Reference

### Core Modules

#### `config.py`
**Purpose:** Database connection and configuration management

**Key Functions:**
```python
def get_database_connection():
    """Create and return active psycopg2 connection"""
    # Returns: Connection object or raises exception
    
def close_database_connection(conn):
    """Safely close psycopg2 connection"""
```

**Configuration Variables:**
```python
DB_HOST = "localhost"                    # PostgreSQL server address
DB_PORT = "5432"                         # PostgreSQL port
DB_NAME = "trading_pipeline"             # Database name
DB_USER = "postgres"                     # Database user
DB_PASSWORD = "postgres"                 # Database password

DB_SCHEMA_BRONZE = "bronze"              # Bronze schema name
DB_SCHEMA_SILVER = "silver"              # Silver schema name
DB_SCHEMA_GOLD = "gold"                  # Gold schema name

TIINGO_API_KEY = ""                      # API key for Tiingo
TIINGO_BASE_URL = "https://api.tiingo.com/tiingo/daily"
```

**Environment Variables:**
- Loaded from `.env` file using `python-dotenv`
- Format: `KEY=value` (one per line)
- Comments with `#`

---

#### `utils.py`
**Purpose:** Constants and metadata for the pipeline

**Key Variables:**
```python
labels = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'SPY', 'JPM']
stooq_label_map = {
    'AAPL': 'aapl.us',
    'MSFT': 'msft.us',
    # ... etc
}

SILVER_COLUMN_LABELS = [
    "ticker", "date", "open_price", "high_price", 
    "low_price", "close_price", "volume", 
    "ingestion_timestamp", "source_name"
]

GOLD_KPI_LABELS = [
    "sma_12m", "sma_24m", "monthly_return", 
    "rolling_volatility_12m", "running_peak_close", 
    "drawdown", "range_percent", "invalid_ohlc_flag"
]
```

---

#### `bronze_layer.py`
**Purpose:** Extract and ingest raw data from sources

**Key Functions:**
```python
def extract_csv_to_dataframe():
    """Extract data from CSV file into pandas DataFrame
    Returns: DataFrame or None if file not found
    """

def extract_api_to_dataframe():
    """Fetch data from Stooq API for all configured tickers
    Returns: Merged DataFrame from all tickers
    """

def ingest_dataframe_to_bronze(df, table_name):
    """Insert DataFrame into bronze table in PostgreSQL
    Args:
        df: pandas DataFrame
        table_name: "bronze.ohlcv_csv_raw" or "bronze.ohlcv_api_raw"
    """
```

**Data Flow:**
```
CSV File / API ──> pandas.DataFrame ──> bronze table (all TEXT)
```

---

#### `silver_layer.py`
**Purpose:** Transform and clean data for business use

**Key Functions:**
```python
def transform_and_clean_to_silver(csv_df, api_df):
    """Transform and merge bronze data into silver layer
    
    Performs:
    - Type conversion (TEXT → DATE, FLOAT, BIGINT)
    - OHLC validation
    - Outlier detection
    - Null handling
    
    Args:
        csv_df: DataFrame from bronze CSV data
        api_df: DataFrame from bronze API data
        
    Returns: Cleaned and merged DataFrame
    """
```

**Validation Rules:**
- `open_price <= high_price` AND `high_price >= close_price`
- `low_price <= high_price`
- `low_price <= open_price` AND `low_price <= close_price`
- All prices ≥ 0
- Volume ≥ 0
- Valid date format

---

#### `gold_layer.py`
**Purpose:** Calculate KPIs and prepare business analytics data

**Key Functions:**
```python
def calculate_kpis_to_gold(silver_df):
    """Calculate all KPIs from silver data
    
    Calculates 8 indicators:
    1. SMA 12M - Simple Moving Average (12 months)
    2. SMA 24M - Simple Moving Average (24 months)
    3. Monthly Return - Month-over-month % change
    4. Rolling Volatility 12M - 12-month standard deviation
    5. Running Peak Close - Cumulative maximum
    6. Drawdown - % decline from peak
    7. Range Percent - (High - Low) / Close * 100
    8. Invalid OHLC Flag - Data quality indicator
    
    Args: silver_df from silver_layer
    Returns: DataFrame with all KPIs calculated
    """
```

**KPI Calculation Details:**
- Moving averages use 252 trading days (≈12 months)
- Volatility calculated as rolling standard deviation
- Drawdown: `(close - peak) / peak`
- Returns use log returns for statistical accuracy
- Invalid flags set to 1 if OHLC validation fails

---

#### `main.py`
**Purpose:** Orchestrate the complete pipeline

**Key Functions:**
```python
def run_full_pipeline():
    """Execute Bronze → Silver → Gold pipeline
    
    Steps:
    1. Extract CSV and API data to bronze layer
    2. Transform/clean to silver layer
    3. Calculate KPIs to gold layer
    4. Print execution summary
    5. Cleanup CSV files
    """

def get_table_row_count(table_name):
    """Query row count from database table
    Args: table_name like "silver.ohlcv_cleaned"
    Returns: Integer row count
    """
```

---

### API Modules

#### `api/app.py`
Entry point for Flask application

```python
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000, host="0.0.0.0")
```

---

#### `api/__init__.py`
Flask app factory and blueprint registration

```python
def create_app():
    """Create and configure Flask application
    
    Enables:
    - CORS for cross-origin requests
    - Blueprint registration (market_data, kpi, indicators)
    
    Returns: Configured Flask app instance
    """
```

---

#### `routes/market_data.py`
Endpoints: `/api/ohlcv`

**Implements:**
- Get OHLCV data from silver layer
- Query parameters: ticker, start_date, end_date, limit
- Response: JSON with count and data array

---

#### `routes/kpi.py`
Endpoints: `/api/kpis`

**Implements:**
- Get KPI-enriched data from gold layer
- Query parameters: ticker, start_date, end_date, limit
- Response: JSON with count and KPI data

---

#### `routes/indicators.py`
Endpoints: `/api/monthly-returns` and others

**Implements:**
- Monthly returns calculation
- Technical indicator computations
- Requires ticker parameter

---

## Configuration

### Environment Variables (`.env`)

```env
# PostgreSQL Database Configuration
DB_HOST=localhost           # Server hostname (usually localhost for local)
DB_PORT=5432               # PostgreSQL default port
DB_NAME=trading_pipeline   # Database name to create
DB_USER=postgres           # Database user (default: postgres)
DB_PASSWORD=postgres       # User password

# API Keys
TIINGO_API_KEY=abc123xyz   # Get from https://www.tiingo.com/
```

### Python Configuration (`config.py`)

**Modify these constants to change default behavior:**

```python
# Database Settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Data Source Settings
API_INTERVAL = "d"                          # "d" = daily data
API_START_DATE = "19000101"                  # Start from beginning
TIINGO_START_DATE = "1900-01-01"             # Earliest available

# Schema Names
DB_SCHEMA_BRONZE = "bronze"
DB_SCHEMA_SILVER = "silver"
DB_SCHEMA_GOLD = "gold"
```

---

## Troubleshooting

### Issue: "password authentication failed for user 'postgres'"

**Solution:**
1. Check `.env` file has correct password
2. Verify PostgreSQL service is running:
   ```bash
   Get-Service postgresql* | Select Status
   ```
3. If running but password wrong, reset PostgreSQL password:
   - Stop PostgreSQL service
   - Use `pg_resetwal` or reinstall

---

### Issue: "Could not connect to server: Connection refused"

**Solution:**
1. PostgreSQL service not running - Start it:
   ```bash
   Start-Service postgres*
   ```
2. Wrong host/port in `.env`
3. Firewall blocking connection

---

### Issue: "Database 'trading_pipeline' does not exist"

**Solution:**
```bash
# Create database manually
psql -U postgres -h localhost
CREATE DATABASE trading_pipeline;
```

---

### Issue: "No data returned from API"

**Possible Causes:**
1. CSV file not in `data/` directory
2. API key invalid or rate limited
3. Stooq API temporarily down

**Solutions:**
- Verify `data/ohlcv_data.csv` exists
- Check Tiingo API key validity
- Run pipeline with CSV only (comment out API extraction)

---

### Issue: "Float: 'NaN'" or calculation errors

**Solution:**
- Ensure data has valid OHLCV values
- Check for null/missing values in source data
- Verify date ordering is correct (ascending)

---

## Database Queries Reference

### Query Data by Ticker

```sql
-- Get latest OHLCV for AAPL
SELECT * FROM silver.ohlcv_cleaned 
WHERE ticker = 'AAPL' 
ORDER BY date DESC 
LIMIT 10;
```

### Query KPIs

```sql
-- Get KPIs showing drawdown for MSFT
SELECT date, close_price, sma_12m, drawdown 
FROM gold.ohlcv_kpis 
WHERE ticker = 'MSFT' AND drawdown < 0 
ORDER BY date DESC;
```

### Data Quality Check

```sql
-- Count invalid OHLCV records
SELECT ticker, COUNT(*) as invalid_count 
FROM gold.ohlcv_kpis 
WHERE invalid_ohlc_flag = 1 
GROUP BY ticker;
```

### Row Counts by Layer

```sql
SELECT 'Bronze CSV' as layer, COUNT(*) as rows FROM bronze.ohlcv_csv_raw
UNION ALL
SELECT 'Bronze API', COUNT(*) FROM bronze.ohlcv_api_raw
UNION ALL
SELECT 'Silver', COUNT(*) FROM silver.ohlcv_cleaned
UNION ALL
SELECT 'Gold', COUNT(*) FROM gold.ohlcv_kpis;
```

---

## File Structure

```
PFE/DATA/v4/
├── config.py                    # Configuration & DB connection
├── utils.py                     # Constants and metadata
├── bronze_layer.py              # Raw data ingestion
├── silver_layer.py              # Data transformation & cleaning
├── gold_layer.py                # KPI calculations
├── main.py                      # Pipeline orchestrator
├── start_api.py                 # Flask API entry point
├── run_api.py                   # Alternative API runner
├── setup_database.sql           # Database schema creation
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (DO NOT COMMIT)
├── DOCUMENTATION.md             # This file
├── api/
│   ├── __init__.py             # Flask app factory
│   ├── app.py                  # Flask application logic
│   └── __pycache__/
├── routes/
│   ├── __init__.py
│   ├── data.py                 # Data routes (unused in v4)
│   ├── market_data.py          # OHLCV endpoints
│   ├── kpi.py                  # KPI endpoints
│   ├── indicators.py           # Technical indicators
│   └── __pycache__/
├── data-profiling/
│   ├── app.py                  # Data profiling tool
│   └── gold_report.html        # Generated profiling report
├── data/                       # CSV data directory (create if needed)
└── __pycache__/
```

---

## Support & Maintenance

### Regular Maintenance Tasks

1. **Health Check** - Run monthly:
   ```bash
   python main.py
   ```

2. **Database Cleanup** - Remove old data:
   ```sql
   DELETE FROM bronze.ohlcv_csv_raw WHERE date < '2020-01-01';
   VACUUM ANALYZE;
   ```

3. **Backup Database**:
   ```bash
   pg_dump trading_pipeline > backup.sql
   ```

### Adding New Tickers

1. Edit `utils.py`:
   ```python
   labels = ['AAPL', 'MSFT', ..., 'NEW_TICKER']
   stooq_label_map = {..., 'NEW_TICKER': 'new_ticker.us'}
   ```

2. Re-run pipeline:
   ```bash
   python main.py
   ```

---

## Performance Tips

### Optimize Queries

Add indexes for common queries:
```sql
CREATE INDEX idx_silver_ticker_date 
ON silver.ohlcv_cleaned(ticker, date DESC);

CREATE INDEX idx_gold_ticker_date 
ON gold.ohlcv_kpis(ticker, date DESC);
```

### Improve Data Load Speed

- Increase `batch_size` in bronze_layer.py
- Use `psycopg2` connection pooling
- Run on SSD storage

### Monitor Performance

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname IN ('bronze', 'silver', 'gold')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## License & Credits

**Project Type:** Financial Data Pipeline (PFE Project)
**Architecture:** Medallion Pattern (Bronze → Silver → Gold)
**Technologies:** Python, PostgreSQL, Flask, pandas
**Data Sources:** CSV files, Stooq API, Tiingo API

---

## Contact & Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review error messages in console output
3. Check `.env` configuration
4. Verify database connectivity

---

**Last Updated:** February 2026
**Version:** 4.0
**Status:** Production Ready

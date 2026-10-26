"""Constants used by the pipeline (tickers, column names, labels)."""

# Liste des tickers financiers à extraire
labels = [
    'AAPL',   # Apple Inc.
    'MSFT',   # Microsoft Corporation
    'GOOG',   # Alphabet Inc.
    'AMZN',   # Amazon.com Inc.
    'TSLA',   # Tesla Inc.
    'SPY',    # S&P 500 ETF Trust
    'JPM',    # JPMorgan Chase & Co.
]

# Correspondance des labels compatibles avec Stooq (actions US : minuscules + .us)
stooq_label_map = {
    'AAPL': 'aapl.us',  # Ticker Apple pour Stooq
    'MSFT': 'msft.us',  # Ticker Microsoft pour Stooq
    'GOOG': 'goog.us',  # Ticker Alphabet pour Stooq
    'AMZN': 'amzn.us',  # Ticker Amazon pour Stooq
    'TSLA': 'tsla.us',  # Ticker Tesla pour Stooq
    'SPY':  'spy.us',   # Ticker ETF S&P 500 pour Stooq
    'JPM':  'jpm.us',   # Ticker JPMorgan pour Stooq
}

# Noms des trois schémas de l'architecture Medallion dans PostgreSQL
SCHEMA_NAMES = ["bronze", "silver", "gold"]  # Liste des noms de schémas

# Noms complets des tables du schéma bronze
BRONZE_TABLE_NAMES = [
    "bronze.ohlcv_csv_raw",   # Table de données brutes CSV
    "bronze.ohlcv_api_raw",   # Table de données brutes API
]

# Noms complets des tables du schéma silver
SILVER_TABLE_NAMES = [
    "silver.ohlcv_cleaned",   # Table de données OHLCV nettoyées
]

# Noms complets des tables du schéma gold
GOLD_TABLE_NAMES = [
    "gold.ohlcv_kpis",   # Table de données KPI
]

# Colonnes standardisées utilisées dans la couche Silver
SILVER_COLUMN_LABELS = [
    "ticker",                # Ticker/symbole (ex: AAPL, MSFT)
    "date",                  # Date de la bougie (format DATE)
    "open_price",            # Prix d'ouverture de la période
    "high_price",            # Prix le plus haut de la période
    "low_price",             # Prix le plus bas de la période
    "close_price",           # Prix de clôture de la période
    "volume",                # Volume échangé sur la période
    "ingestion_timestamp",   # Horodatage d'ingestion depuis la couche bronze
    "source_name",           # Nom de la source d'origine
]

# Labels des 8 KPIs calculés dans la couche Gold (source : PDF Visual Strategy)
GOLD_KPI_LABELS = [
    "sma_12m",                  # Moyenne mobile simple sur 12 mois
    "sma_24m",                  # Moyenne mobile simple sur 24 mois
    "monthly_return",           # Rendement mensuel vs mois précédent (%)
    "rolling_volatility_12m",   # Écart-type glissant sur 12 mois
    "running_peak_close",       # Plus haut cours cumulatif jusqu'à cette date
    "drawdown",                 # Perte en % depuis le pic : (Close / Peak) - 1
    "range_percent",            # Amplitude : (High - Low) / Close * 100
    "invalid_ohlc_flag",        # 1 si OHLC invalide, 0 si valide
]

# Identifiants des sources de données utilisés comme métadonnées
SOURCE_LABELS = {
    "csv": "CSV_FILE",      # Étiquette source fichier CSV
    "api": "REST_API",      # Étiquette source API REST
}

# Types de visuels recommandés (source : PDF Visual Strategy)
CHART_TYPE_LABELS = [
    "Candlestick + Volume",        # Graphique en chandelier avec volume
    "Line Chart (Trend)",          # Graphique de tendance linéaire
    "Returns & Histogram",         # Graphique de rendements avec histogramme
    "Rolling Volatility",          # Graphique de volatilité glissante
    "Drawdown Chart",              # Graphique de visualisation du drawdown
]

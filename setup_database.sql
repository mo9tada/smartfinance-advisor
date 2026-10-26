-- Simple DB setup (schemas)

-- Créer le schéma Bronze pour le stockage des données brutes
CREATE SCHEMA IF NOT EXISTS bronze;  -- Créer le schéma bronze

-- Créer le schéma Silver pour le stockage des données nettoyées
CREATE SCHEMA IF NOT EXISTS silver;  -- Créer le schéma silver

-- Créer le schéma Gold pour le stockage des données prêtes pour les affaires
CREATE SCHEMA IF NOT EXISTS gold;  -- Créer le schéma gold

-- Supprimer et créer la table Bronze CSV brute (toutes les colonnes en TEXT)
DROP TABLE IF EXISTS bronze.ohlcv_csv_raw;  -- Supprimer la table si elle existe
CREATE TABLE IF NOT EXISTS bronze.ohlcv_csv_raw (
    ticker               TEXT,  -- Ticker label (ex: JPM)
    "Date"               TEXT,  -- Colonne date en texte
    "Open"               TEXT,  -- Colonne prix d'ouverture en texte
    "High"               TEXT,  -- Colonne prix le plus haut en texte
    "Low"                TEXT,  -- Colonne prix le plus bas en texte
    "Close"              TEXT,  -- Colonne prix de clôture en texte
    "Volume"             TEXT,  -- Colonne volume en texte
    ingestion_timestamp  TEXT,  -- Colonne horodatage d'ingestion en texte
    source_name          TEXT,  -- Colonne nom de source en texte
    source_file          TEXT   -- Colonne fichier source en texte
);

-- Supprimer et créer la table Bronze API brute (toutes les colonnes en TEXT)
DROP TABLE IF EXISTS bronze.ohlcv_api_raw;  -- Supprimer la table si elle existe
CREATE TABLE IF NOT EXISTS bronze.ohlcv_api_raw (
    ticker               TEXT,  -- Ticker label (ex: JPM)
    "Date"               TEXT,  -- Colonne date en texte
    "Open"               TEXT,  -- Colonne prix d'ouverture en texte
    "High"               TEXT,  -- Colonne prix le plus haut en texte
    "Low"                TEXT,  -- Colonne prix le plus bas en texte
    "Close"              TEXT,  -- Colonne prix de clôture en texte
    "Volume"             TEXT,  -- Colonne volume en texte
    ingestion_timestamp  TEXT,  -- Colonne horodatage d'ingestion en texte
    source_name          TEXT,  -- Colonne nom de source en texte
    source_file          TEXT   -- Colonne fichier source en texte
);

-- Supprimer et créer la table Silver nettoyée (types SQL appropriés)
DROP TABLE IF EXISTS silver.ohlcv_cleaned;  -- Supprimer la table si elle existe
CREATE TABLE IF NOT EXISTS silver.ohlcv_cleaned (
    ticker               TEXT,      -- Ticker label (ex: JPM)
    date                 DATE,      -- Colonne date en type DATE
    open_price           FLOAT,    -- Colonne prix d'ouverture en FLOAT
    high_price           FLOAT,    -- Colonne prix le plus haut en FLOAT
    low_price            FLOAT,     -- Colonne prix le plus bas en FLOAT
    close_price          FLOAT,    -- Colonne prix de clôture en FLOAT
    volume               BIGINT,    -- Colonne volume en BIGINT
    ingestion_timestamp  TIMESTAMP, -- Colonne horodatage d'ingestion en TIMESTAMP
    source_name          TEXT       -- Colonne nom de source en TEXT
);

-- Supprimer et créer la table Gold KPI (tous les KPI avec types SQL appropriés)
DROP TABLE IF EXISTS gold.ohlcv_kpis;  -- Supprimer la table si elle existe
CREATE TABLE IF NOT EXISTS gold.ohlcv_kpis (
    ticker                  TEXT,     -- Ticker label (ex: JPM)
    date                    DATE,     -- Colonne date en type DATE
    open_price              FLOAT,    -- Colonne prix d'ouverture en FLOAT
    high_price              FLOAT,    -- Colonne prix le plus haut en FLOAT
    low_price               FLOAT,    -- Colonne prix le plus bas en FLOAT
    close_price             FLOAT,    -- Colonne prix de clôture en FLOAT
    volume                  BIGINT,   -- Colonne volume en BIGINT
    sma_12m                 FLOAT,   -- Colonne moyenne mobile 12 mois en FLOAT
    sma_24m                 FLOAT,   -- Colonne moyenne mobile 24 mois en FLOAT
    monthly_return          FLOAT,   -- Colonne rendement mensuel en FLOAT
    rolling_volatility_12m  FLOAT,   -- Colonne volatilité glissante en FLOAT
    running_peak_close      FLOAT,   -- Colonne pic cumulatif en FLOAT
    drawdown                FLOAT,   -- Colonne drawdown en FLOAT
    range_percent           FLOAT,   -- Colonne pourcentage d'amplitude en FLOAT
    invalid_ohlc_flag       INTEGER  -- Colonne drapeau OHLC invalide en INTEGER
);

SELECT table_schema, table_name  -- Sélectionner les noms de schéma et de table
FROM information_schema.tables  -- Depuis les tables information_schema
WHERE table_schema IN ('bronze','silver','gold', 'app_auth')  -- Filtrer par schémas
ORDER BY table_schema, table_name;  -- Trier par schéma et nom de table

-- Créer le schéma app_auth pour s'interfacer avec l'authentification
CREATE SCHEMA IF NOT EXISTS app_auth;

CREATE TABLE IF NOT EXISTS app_auth.users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    role VARCHAR(50) DEFAULT 'viewer',
    status VARCHAR(50) DEFAULT 'pending',
    matricule VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    reset_code VARCHAR(10),
    reset_code_expires_at TIMESTAMP,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


# Pipeline de données Architecture Medallion — Données financières OHLCV

Pipeline complet de données financières utilisant l'architecture Medallion (Bronze → Silver → Gold) pour traiter des données OHLCV (Open, High, Low, Close, Volume) depuis un fichier CSV et une API REST (Stooq), avec stockage dans PostgreSQL.

## Structure du projet

```
V2/
├── utils.py              # Toutes les étiquettes, constantes et noms de colonnes
├── config.py             # Paramètres de connexion PostgreSQL + API et fonctions
├── bronze_layer.py       # Ingestion de données brutes depuis CSV et API
├── silver_layer.py       # Transformation et nettoyage des données
├── gold_layer.py         # Calcul des KPI et analyses prêtes pour les affaires
├── main.py               # Orchestrateur du pipeline (Bronze → Silver → Gold)
├── setup_database.sql    # Script SQL pour créer les schémas et tables
├── requirements.txt      # Dépendances Python
├── README.md             # Ce fichier
└── data/
    └── ohlcv_data.csv    # Fichier CSV source (à placer ici)
```

## Installation

### 1. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 2. Configuration PostgreSQL

#### Créer la base de données

```sql
CREATE DATABASE trading_pipeline;
```

#### Exécuter le script de configuration

```bash
psql -U your_username -d trading_pipeline -f setup_database.sql
```

Ou exécuter manuellement les commandes SQL depuis `setup_database.sql` dans votre client PostgreSQL.

### 3. Configuration

Éditer `config.py` et mettre à jour les paramètres suivants :

```python
DB_HOST = "localhost"           # Adresse du serveur PostgreSQL
DB_PORT = "5432"                # Port PostgreSQL
DB_NAME = "trading_pipeline"    # Nom de la base de données
DB_USER = "your_username"       # Nom d'utilisateur PostgreSQL
DB_PASSWORD = "your_password"   # Mot de passe PostgreSQL

API_INTERVAL = "d"              # Intervalle des données ("d" = daily)
CSV_FILE_PATH = "data/ohlcv_data.csv"  # Chemin vers le fichier CSV
```

### 4. Préparer le fichier CSV

Créer le dossier `data/` à la racine du projet et y placer votre fichier CSV avec les colonnes suivantes :

**Colonnes requises :**
- `Date` : Date au format YYYY-MM-DD
- `Open` : Prix d'ouverture
- `High` : Prix le plus haut
- `Low` : Prix le plus bas
- `Close` : Prix de clôture
- `Volume` : Volume échangé

**Exemple de format :**
```csv
Date,Open,High,Low,Close,Volume
2024-01-01,100.50,102.30,99.80,101.20,1500000
2024-01-02,101.20,103.10,100.90,102.50,1800000
```

## Exécution

### Exécuter le pipeline complet

```bash
python main.py
```

Le pipeline exécute automatiquement les trois couches dans l'ordre :
1. **Bronze** : Ingestion des données brutes depuis CSV et API
2. **Silver** : Transformation et nettoyage des données
3. **Gold** : Calcul des KPI et analyses métier

**Note importante :** Le fichier CSV source sera automatiquement supprimé à la fin du pipeline si tout s'est bien passé.

## Ordre d'exécution du pipeline

```
CSV File ──┐
           ├──> Bronze Layer ──> PostgreSQL (bronze schema)
API Stooq ─┘         │
                     │
                     ▼
            Silver Layer ──> PostgreSQL (silver schema)
                     │
                     ▼
            Gold Layer ──> PostgreSQL (gold schema)
                     │
                     ▼
            CSV File Deleted (end of main.py)
```

## Table des tickers

Le fichier `utils.py` contient la liste des tickers financiers supportés :

| Ticker | Nom complet | Format Stooq |
|--------|-------------|--------------|
| AAPL   | Apple Inc. | aapl.us |
| MSFT   | Microsoft Corporation | msft.us |
| GOOG   | Alphabet Inc. | goog.us |
| AMZN   | Amazon.com Inc. | amzn.us |
| TSLA   | Tesla Inc. | tsla.us |
| SPY    | S&P 500 ETF Trust | spy.us |
| JPM    | JPMorgan Chase & Co. | jpm.us |

Les tickers extraits proviennent de `utils.py` (`labels` + `stooq_label_map`).

## Table des KPI

Les 8 KPI calculés dans la couche Gold (source : PDF "Visual Strategy — The Five Essential Charts") :

| KPI | Description | Formule |
|-----|-------------|---------|
| `sma_12m` | Moyenne mobile simple sur 12 mois | `rolling_mean(close_price, window=12)` |
| `sma_24m` | Moyenne mobile simple sur 24 mois | `rolling_mean(close_price, window=24)` |
| `monthly_return` | Rendement mensuel (%) | `(close_price - previous_close) / previous_close * 100` |
| `rolling_volatility_12m` | Volatilité glissante sur 12 mois | `rolling_std(monthly_return, window=12)` |
| `running_peak_close` | Plus haut cours cumulatif | `close_price.cummax()` |
| `drawdown` | Perte depuis le pic (%) | `(close_price / running_peak_close) - 1` |
| `range_percent` | Amplitude quotidienne (%) | `(high_price - low_price) / close_price * 100` |
| `invalid_ohlc_flag` | Drapeau OHLC invalide | `1 si high_price < max(open,high,low,close), sinon 0` |

## Structure des schémas PostgreSQL

### Schéma Bronze (`bronze`)

**Table : `ohlcv_csv_raw`**
- Toutes les colonnes en type `TEXT`
- Colonnes : `Date`, `Open`, `High`, `Low`, `Close`, `Volume`, `ingestion_timestamp`, `source_name`, `source_file`

**Table : `ohlcv_api_raw`**
- Toutes les colonnes en type `TEXT`
- Colonnes : `Date`, `Open`, `High`, `Low`, `Close`, `Volume`, `ingestion_timestamp`, `source_name`, `source_file`

### Schéma Silver (`silver`)

**Table : `ohlcv_cleaned`**
- Types SQL appropriés (DATE, FLOAT, BIGINT, TIMESTAMP, TEXT)
- Colonnes : `date`, `open_price`, `high_price`, `low_price`, `close_price`, `volume`, `ingestion_timestamp`, `source_name`
- Données fusionnées, nettoyées et transformées

### Schéma Gold (`gold`)

**Table : `ohlcv_kpis`**
- Toutes les colonnes OHLCV + les 8 KPI calculés
- Colonnes : `date`, `open_price`, `high_price`, `low_price`, `close_price`, `volume`, `sma_12m`, `sma_24m`, `monthly_return`, `rolling_volatility_12m`, `running_peak_close`, `drawdown`, `range_percent`, `invalid_ohlc_flag`

## Requêtes de vérification utiles

### Compter les lignes dans chaque couche

```sql
-- Bronze CSV
SELECT COUNT(*) FROM bronze.ohlcv_csv_raw;

-- Bronze API
SELECT COUNT(*) FROM bronze.ohlcv_api_raw;

-- Silver
SELECT COUNT(*) FROM silver.ohlcv_cleaned;

-- Gold
SELECT COUNT(*) FROM gold.ohlcv_kpis;
```

### Vérifier les données Bronze (premières lignes)

```sql
SELECT * FROM bronze.ohlcv_csv_raw LIMIT 5;
SELECT * FROM bronze.ohlcv_api_raw LIMIT 5;
```

### Vérifier les données Silver (premières lignes)

```sql
SELECT * FROM silver.ohlcv_cleaned ORDER BY date ASC LIMIT 10;
```

### Vérifier les KPI Gold (premières lignes)

```sql
SELECT 
    date, 
    close_price, 
    sma_12m, 
    sma_24m, 
    monthly_return, 
    drawdown 
FROM gold.ohlcv_kpis 
ORDER BY date DESC 
LIMIT 10;
```

### Vérifier les données invalides

```sql
SELECT COUNT(*) 
FROM gold.ohlcv_kpis 
WHERE invalid_ohlc_flag = 1;
```

### Statistiques des KPI

```sql
SELECT 
    AVG(monthly_return) as avg_monthly_return,
    AVG(rolling_volatility_12m) as avg_volatility,
    MIN(drawdown) as max_drawdown,
    MAX(range_percent) as max_range
FROM gold.ohlcv_kpis;
```

## Notes importantes

- **Tous les fichiers Python** contiennent des commentaires français sur chaque ligne
- **Le fichier CSV est supprimé automatiquement** à la fin du pipeline si tout s'est bien passé
- **La couche Bronze** stocke toutes les données en type `TEXT` sans aucune modification
- **La couche Silver** fusionne les données CSV et API, puis les nettoie et transforme
- **La couche Gold** calcule les 8 KPI métier pour l'analyse financière
- Le pipeline utilise uniquement des bibliothèques Python de base (pandas, requests, psycopg2)

## Dépannage

### Erreur de connexion PostgreSQL
- Vérifier que PostgreSQL est en cours d'exécution
- Vérifier les paramètres dans `config.py`
- Vérifier que la base de données et les schémas existent

### Erreur API Stooq
- Vérifier la connexion Internet
- Vérifier que le ticker est valide (format : `ticker.us`)
- Vérifier l'URL de l'API dans `config.py`

### Erreur fichier CSV
- Vérifier que le fichier existe à `data/ohlcv_data.csv`
- Vérifier que le fichier contient les colonnes requises
- Vérifier le format des dates (YYYY-MM-DD)

## Licence

Ce projet est fourni tel quel à des fins éducatives.

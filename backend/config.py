"""Project config (DB + Stooq settings)."""

import os  # Importer os pour accéder aux variables d'environnement
import psycopg2  # Importer la bibliothèque psycopg2 pour la connexion PostgreSQL
from dotenv import load_dotenv  # Importer dotenv pour charger les variables d'environnement

# Load values from .env (if present)
# Force load from the exact path (project root)
# config.py is now in backend/, so root is ../
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path, override=True)

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  # Adresse du serveur de base de données
DB_PORT = os.getenv("DB_PORT", "5432")  # Numéro de port de la base de données
DB_NAME = os.getenv("DB_NAME", "trading_pipeline")  # Nom de la base de données
DB_USER = os.getenv("DB_USER", "postgres")  # Nom d'utilisateur de la base de données
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")  # Mot de passe de la base de données

# Tiingo API Key
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY", "")  # Clé API Tiingo
TIINGO_BASE_URL = "https://api.tiingo.com/tiingo/daily"  # Base URL for Tiingo EOD
TIINGO_START_DATE = "1900-01-01"  # Requested start date (earliest available will be returned)

DB_SCHEMA_BRONZE = "bronze"  # Nom du schéma bronze
DB_SCHEMA_SILVER = "silver"  # Nom du schéma silver
DB_SCHEMA_GOLD = "gold"  # Nom du schéma gold

# Security Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    # Never fall back to a hard-coded secret: tokens signed with a public
    # default could be forged. Generate a per-process key instead (sessions
    # reset on restart) and ask the operator to configure a real one.
    import secrets
    JWT_SECRET_KEY = secrets.token_urlsafe(48)
    print("WARNING: JWT_SECRET_KEY is not set; using a random key for this process.")
JWT_ACCESS_TOKEN_EXPIRES = 28800  # 8 hours in seconds

# Flask-Mail Configuration (Example SMTP)
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME or "noreply@sfa.com"

API_BASE_URL = "https://stooq.com/q/d/l/"  # URL de base pour l'API Stooq
# NOTE: tickers are taken from utils.py (labels + stooq_label_map)
API_INTERVAL = "d"  # Intervalle de données (d = daily)
# Stooq expects YYYYMMDD for d1/d2 parameters
API_START_DATE = "19000101"  # Start date requested (earliest available will be returned)



def get_database_connection():
    """Create and return active psycopg2 connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"DB connection error: {e}")
        raise

def close_database_connection(conn):
    """Safely close psycopg2 connection"""
    if conn is not None:
        try:
            conn.close()
        except Exception as e:
            print(f"DB close error: {e}")

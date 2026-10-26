"""Initialisation de l'API Flask."""

import sys
import os

# Add the current directory and backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_cors import CORS
import config
from app_init import bcrypt, jwt, mail

def create_app():
    """Créer et configurer l'application Flask."""
    app = Flask(__name__)
    
    # Configuration
    app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.JWT_ACCESS_TOKEN_EXPIRES
    app.config['MAIL_SERVER'] = config.MAIL_SERVER
    app.config['MAIL_PORT'] = config.MAIL_PORT
    app.config['MAIL_USE_TLS'] = config.MAIL_USE_TLS
    app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER

    # Initialize Extensions
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:4200", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Importation et enregistrement des routes (blueprints)
    try:
        from routes.market_data import bp as market_data_bp
        from routes.kpi import bp as kpi_bp
        from routes.indicators import bp as indicators_bp
        from routes.forecast import bp as forecast_bp
        from routes.auth import bp as auth_bp
        from routes.admin import bp as admin_bp
        from routes.ingestion import bp as ingestion_bp
        from routes.law_ingestion import bp as law_ingestion_bp
        from routes.notifications import bp as notifications_bp
        from routes.chat import bp as chat_bp
        
        app.register_blueprint(market_data_bp)
        app.register_blueprint(kpi_bp)
        app.register_blueprint(indicators_bp)
        app.register_blueprint(forecast_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp)
        app.register_blueprint(ingestion_bp)
        app.register_blueprint(law_ingestion_bp)
        app.register_blueprint(notifications_bp)
        app.register_blueprint(chat_bp)
        
        print("✅ All blueprints registered successfully!")
    except ImportError as e:
        print(f"❌ Error importing blueprints: {e}")
        raise
    
    return app

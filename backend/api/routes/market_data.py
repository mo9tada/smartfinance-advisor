"""Points de terminaison pour les données OHLCV."""

from flask import Blueprint, jsonify, request
import pandas as pd
from config import get_database_connection, close_database_connection

bp = Blueprint("market_data", __name__, url_prefix="/api")

@bp.route("/ohlcv", methods=["GET"])
def get_ohlcv():
    """Récupérer les données OHLCV depuis la table silver."""
    try:
        ticker = request.args.get("ticker", None)
        start_date = request.args.get("start_date", None)
        end_date = request.args.get("end_date", None)
        limit = request.args.get("limit", None, type=int)
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT ticker, date, open_price, high_price, low_price, close_price, volume, source_name FROM silver.ohlcv_cleaned WHERE 1=1"
        params = []
        
        if ticker:
            query += " AND ticker = %s"
            params.append(ticker)
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY date ASC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        close_database_connection(conn)
        
        # Format as list of dicts
        result = []
        if rows:
            columns = ["ticker", "date", "open_price", "high_price", "low_price", "close_price", "volume", "source_name"]
            for row in rows:
                result.append(dict(zip(columns, row)))
        
        return jsonify({
            "status": "success",
            "count": len(result),
            "data": result
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@bp.route("/ohlcv/tickers", methods=["GET"])
def get_tickers():
    """Get list of unique tickers in the database."""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ticker FROM silver.ohlcv_cleaned ORDER BY ticker ASC")
        tickers = [row[0] for row in cursor.fetchall()]
        cursor.close()
        close_database_connection(conn)
        
        return jsonify({
            "status": "success",
            "tickers": tickers
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
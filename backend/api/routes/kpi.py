"""Points de terminaison pour les données KPI (indicateurs de performance)."""

from flask import Blueprint, jsonify, request
import pandas as pd
from config import get_database_connection, close_database_connection

bp = Blueprint("kpi", __name__, url_prefix="/api")

@bp.route("/kpis", methods=["GET"])
def get_kpis():
    """Récupérer les données KPI depuis la table gold."""
    try:
        ticker = request.args.get("ticker", None)
        start_date = request.args.get("start_date", None)
        end_date = request.args.get("end_date", None)
        limit = request.args.get("limit", None, type=int)
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT 
                ticker, date, open_price, high_price, low_price, close_price, volume,
                sma_12m, sma_24m, monthly_return, rolling_volatility_12m,
                running_peak_close, drawdown, range_percent, invalid_ohlc_flag
            FROM gold.ohlcv_kpis
            WHERE 1=1
        """
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
            columns = [
                "ticker", "date", "open_price", "high_price", "low_price", "close_price", "volume",
                "sma_12m", "sma_24m", "monthly_return", "rolling_volatility_12m",
                "running_peak_close", "drawdown", "range_percent", "invalid_ohlc_flag"
            ]
            for row in rows:
                data = dict(zip(columns, row))
                # Convert None values to null
                data = {k: (v if v is not None else None) for k, v in data.items()}
                result.append(data)
        
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

@bp.route("/kpis/summary", methods=["GET"])
def get_kpis_summary():
    """Get summary statistics for KPIs."""
    try:
        ticker = request.args.get("ticker", None)
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                AVG(monthly_return) as avg_return,
                AVG(rolling_volatility_12m) as avg_volatility,
                MIN(drawdown) as max_drawdown,
                MAX(drawdown) as min_drawdown,
                MAX(range_percent) as max_range,
                COUNT(*) as total_rows
            FROM gold.ohlcv_kpis
            WHERE 1=1
        """
        params = []
        
        if ticker:
            query += " AND ticker = %s"
            params.append(ticker)
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        close_database_connection(conn)
        
        if row:
            columns = ["avg_return", "avg_volatility", "max_drawdown", "min_drawdown", "max_range", "total_rows"]
            result = dict(zip(columns, row))
            result = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in result.items()}
        else:
            result = {}
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
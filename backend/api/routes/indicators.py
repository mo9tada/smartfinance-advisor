"""Points de terminaison pour le calcul des indicateurs techniques."""

from flask import Blueprint, jsonify, request
import pandas as pd
from config import get_database_connection, close_database_connection

bp = Blueprint("indicators", __name__, url_prefix="/api")

@bp.route("/monthly-returns", methods=["GET"])
def get_monthly_returns():
    """Calculer les rendements mensuels."""
    try:
        ticker = request.args.get("ticker")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        if not ticker:
            return jsonify({
                "status": "error",
                "message": "ticker parameter is required"
            }), 400
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Query data
        query = """
            SELECT date, close_price FROM silver.ohlcv_cleaned
            WHERE ticker = %s
        """
        params = [ticker]
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY date ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        close_database_connection(conn)
        
        # Convert to DataFrame for calculation
        if not rows:
            return jsonify({
                "status": "success",
                "count": 0,
                "data": []
            }), 200
        
        df = pd.DataFrame(rows, columns=["date", "close_price"])
        df["close_price"] = pd.to_numeric(df["close_price"], errors="coerce")
        
        # Calculate monthly return
        df["monthly_return"] = df["close_price"].pct_change() * 100
        
        # Format result
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": str(row["date"]),
                "close_price": float(row["close_price"]) if pd.notna(row["close_price"]) else None,
                "monthly_return": float(row["monthly_return"]) if pd.notna(row["monthly_return"]) else None
            })
        
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

@bp.route("/sma", methods=["GET"])
def get_sma():
    """Calculer les moyennes mobiles simples (SMA)."""
    try:
        ticker = request.args.get("ticker")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        if not ticker:
            return jsonify({
                "status": "error",
                "message": "ticker parameter is required"
            }), 400
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT date, close_price FROM silver.ohlcv_cleaned
            WHERE ticker = %s
        """
        params = [ticker]
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY date ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        close_database_connection(conn)
        
        if not rows:
            return jsonify({
                "status": "success",
                "count": 0,
                "data": []
            }), 200
        
        df = pd.DataFrame(rows, columns=["date", "close_price"])
        df["close_price"] = pd.to_numeric(df["close_price"], errors="coerce")
        
        # Calculate SMAs
        df["sma_12"] = df["close_price"].rolling(window=12, min_periods=1).mean()
        df["sma_24"] = df["close_price"].rolling(window=24, min_periods=1).mean()
        
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": str(row["date"]),
                "close": float(row["close_price"]) if pd.notna(row["close_price"]) else None,
                "sma_12": float(row["sma_12"]) if pd.notna(row["sma_12"]) else None,
                "sma_24": float(row["sma_24"]) if pd.notna(row["sma_24"]) else None
            })
        
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

@bp.route("/volatility", methods=["GET"])
def get_volatility():
    """Calculer la volatilité glissante."""
    try:
        ticker = request.args.get("ticker")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        if not ticker:
            return jsonify({
                "status": "error",
                "message": "ticker parameter is required"
            }), 400
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT date, close_price FROM silver.ohlcv_cleaned
            WHERE ticker = %s
        """
        params = [ticker]
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY date ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        close_database_connection(conn)
        
        if not rows:
            return jsonify({
                "status": "success",
                "count": 0,
                "data": []
            }), 200
        
        df = pd.DataFrame(rows, columns=["date", "close_price"])
        df["close_price"] = pd.to_numeric(df["close_price"], errors="coerce")
        
        # Calculate monthly returns then volatility
        df["monthly_return"] = df["close_price"].pct_change() * 100
        df["volatility"] = df["monthly_return"].rolling(window=12, min_periods=2).std()
        
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": str(row["date"]),
                "volatility": float(row["volatility"]) if pd.notna(row["volatility"]) else None
            })
        
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

@bp.route("/drawdown", methods=["GET"])
def get_drawdown():
    """Calculer le drawdown (perte maximale depuis le pic)."""
    try:
        ticker = request.args.get("ticker")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        if not ticker:
            return jsonify({
                "status": "error",
                "message": "ticker parameter is required"
            }), 400
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT date, close_price FROM silver.ohlcv_cleaned
            WHERE ticker = %s
        """
        params = [ticker]
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY date ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        close_database_connection(conn)
        
        if not rows:
            return jsonify({
                "status": "success",
                "count": 0,
                "data": []
            }), 200
        
        df = pd.DataFrame(rows, columns=["date", "close_price"])
        df["close_price"] = pd.to_numeric(df["close_price"], errors="coerce")
        
        # Calculate running peak and drawdown
        df["peak"] = df["close_price"].cummax()
        df["drawdown"] = ((df["close_price"] - df["peak"]) / df["peak"]) * 100
        
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": str(row["date"]),
                "close": float(row["close_price"]) if pd.notna(row["close_price"]) else None,
                "peak": float(row["peak"]) if pd.notna(row["peak"]) else None,
                "drawdown": float(row["drawdown"]) if pd.notna(row["drawdown"]) else None
            })
        
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
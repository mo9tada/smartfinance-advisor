"""Forecast route placeholder with prediction logic updated to use dedicated prediction pipeline."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import sys
import os
from api.notification_service import create_notification

# Add predictions module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from predictions.prediction import generate_prediction_and_report

bp = Blueprint("forecast", __name__, url_prefix="/api")


@bp.route("/forecast", methods=["GET"])
@jwt_required()
def get_forecast():
    """Generates simple predictions, saves a PDF report, and formats for the Angular UI."""
    try:
        ticker = (request.args.get("ticker") or "").strip().upper()
        periods = request.args.get("periods", default=30, type=int)
        interval_width = request.args.get("interval_width", default=0.999, type=float)

        if not ticker:
            return jsonify({"status": "error", "message": "ticker parameter is required"}), 400

        # Offload all DB querying, modelling, PDF creation, and JSON shaping to predictions/prediction.py
        result_data = generate_prediction_and_report(
            ticker=ticker,
            periods=periods,
            interval_width=interval_width
        )
        
        # Trigger notification
        create_notification("prediction", f"A new prediction to {periods} days has been generated for {ticker}.")

        return jsonify({
            "status": "success",
            "data": result_data
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500

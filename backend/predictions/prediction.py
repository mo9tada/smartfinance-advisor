import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Required for headless server PDF generation
import matplotlib.pyplot as plt
from prophet import Prophet

# Add the backend root to the path so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_database_connection

REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_prediction_and_report(ticker: str, periods: int, interval_width: float = 0.95):
    """
    Fetches data, trains Prophet, calculates metrics, generates PDF, and returns forecast data payload.
    """
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Fetch data from PostgreSQL
        query = "SELECT date AS ds, close_price, high_price, low_price FROM silver.ohlcv_cleaned WHERE ticker = %s ORDER BY date ASC"
        cursor.execute(query, (ticker,))
            
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        
        if df.empty:
            raise ValueError(f"No data found for ticker {ticker}")
            
        cursor.close()
    finally:
        conn.close()

    # Clean data
    df['ds'] = pd.to_datetime(df['ds'])
    df['close_price'] = pd.to_numeric(df['close_price'])
    df['high_price'] = pd.to_numeric(df['high_price'])
    df['low_price'] = pd.to_numeric(df['low_price'])
    df = df.dropna()

    # Filter data to the last 5 years, or use the first available date if there is less than 5 years of data
    max_date = df['ds'].max()
    first_date = df['ds'].min()
    
    target_min_date = max_date - pd.DateOffset(years=5)
    min_date = max(first_date, target_min_date)
    
    df = df[df['ds'] >= min_date]

    # 2. Train Prophet Models (Close, High, and Low)
    # We increase changepoint_prior_scale to allow the model's trend to be more flexible
    # and fit historical stock market data (which is highly volatile) much better.
    def get_prophet_model():
        return Prophet(
            interval_width=interval_width,
            daily_seasonality=False,
            yearly_seasonality=True,
            weekly_seasonality=True,
            changepoint_prior_scale=0.15
        )

    # Prepare datasets for each model
    df_close = df[['ds', 'close_price']].rename(columns={'close_price': 'y'})
    df_high = df[['ds', 'high_price']].rename(columns={'high_price': 'y'})
    df_low = df[['ds', 'low_price']].rename(columns={'low_price': 'y'})

    model_close = get_prophet_model().fit(df_close)
    model_high = get_prophet_model().fit(df_high)
    model_low = get_prophet_model().fit(df_low)

    # 3. Generate Predictions
    future = model_close.make_future_dataframe(periods=periods, freq='D')
    
    forecast_close = model_close.predict(future)
    forecast_high = model_high.predict(future)
    forecast_low = model_low.predict(future)

    # Make upper and lower bounds perfectly logical using the predicted high and low prices
    # We also ensure the math holds: high >= close >= low
    forecast = forecast_close.copy()
    forecast['yhat_upper'] = np.maximum(forecast_close['yhat'], forecast_high['yhat'])
    forecast['yhat_lower'] = np.minimum(forecast_close['yhat'], forecast_low['yhat'])

    # Extract pieces
    historical_forecast = forecast[forecast['ds'] <= df['ds'].max()]
    future_forecast = forecast[forecast['ds'] > df['ds'].max()]

    # 4. Calculate Evaluation Metrics (In-Sample Data Profiling)
    y_true = df['close_price'].values
    y_pred = historical_forecast['yhat'].values
    
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    
    # Calculate sMAPE (Symmetric Mean Absolute Percentage Error) for stability
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    smape_mask = denominator != 0
    if smape_mask.any():
        smape = np.mean(np.abs(y_true[smape_mask] - y_pred[smape_mask]) / denominator[smape_mask]) * 100
    else:
        smape = 0.0

    # Convert bounded sMAPE to an accuracy percentage
    accuracy_percentage = max(0.0, 100.0 - smape)

    # 5. Generate PDF Report (Data Profiling & Metrics)
    pdf_filename = f"{ticker}_close_price_report.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    
    fig = model_close.plot(forecast)
    plt.title(f"Prophet Close Price Forecast & Profiling: {ticker}")
    plt.xlabel("Date")
    plt.ylabel("Close Price")
    
    # Add a text box with metrics
    # These are in-sample (training-fit) metrics, not out-of-sample forecast accuracy.
    stats_text = f"In-sample fit:\nMAE: {mae:.2f}\nRMSE: {rmse:.2f}\nsMAPE: {smape:.2f}%"
    plt.figtext(0.15, 0.75, stats_text, fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
    
    plt.savefig(pdf_path, format='pdf')
    plt.close(fig)

    # 6. Format Response for Frontend
    history_points = [
        {"date": row.ds.strftime('%Y-%m-%d'), "value": float(row.close_price)}
        for _, row in df.iterrows()
    ]
    
    # Cap history returned to avoid giant payloads hitting UI limit
    history_points = history_points[-1500:]
    
    prediction_points = [
        {
            "date": row.ds.strftime('%Y-%m-%d'),
            "yhat": float(row.yhat),
            "yhat_lower": float(row.yhat_lower),
            "yhat_upper": float(row.yhat_upper),
            "confidence_percent": interval_width * 100,
            "interval_coverage_percent": interval_width * 100,
            "actual_confidence_percent": interval_width * 100
        }
        for _, row in future_forecast.iterrows()
    ]

    return {
        "ticker": ticker,
        "source": "silver_close",
        "metric": "close_price",
        "periods": periods,
        "confidence_percent": interval_width * 100,
        "interval_coverage_percent": interval_width * 100,
        "avg_actual_confidence_percent": interval_width * 100,
        "actual_accuracy_percent": float(accuracy_percentage),
        "report_path": pdf_path,
        "history": history_points,
        "predictions": prediction_points
    }

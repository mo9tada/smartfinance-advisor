export interface OHLCV {
    date: string;
    open_price: number;
    high_price: number;
    low_price: number;
    close_price: number;
    volume: number;
}

export interface KPI {
    kpi_name: string;
    value: number;
}

export interface KPIStats {
    avg_return: number;
    avg_volatility: number;
    max_drawdown: number;
    min_drawdown: number;
    max_range: number;
    total_rows: number;
}

export interface MonthlyReturn {
    date: string;
    close_price: number;
    monthly_return: number;
}

export interface SMA {
    date: string;
    close: number;
    sma_12: number;
    sma_24: number;
}

export interface Volatility {
    date: string;
    volatility: number;
}

export interface Drawdown {
    date: string;
    close: number;
    peak: number;
    drawdown: number;
}

export type PredictionSource = 'silver_close' | 'gold_metric';

export type GoldMetric =
    | 'monthly_return'
    | 'sma_12m'
    | 'sma_24m'
    | 'rolling_volatility_12m'
    | 'drawdown'
    | 'range_percent';

export interface PredictionHistoryPoint {
    date: string;
    value: number;
}

export interface PredictionPoint {
    date: string;
    yhat: number;
    yhat_lower: number;
    yhat_upper: number;
    confidence_percent: number;
    interval_coverage_percent: number;
    actual_confidence_percent: number;
}

export interface PredictionResponse {
    ticker: string;
    source: PredictionSource;
    metric: GoldMetric | null;
    periods: number;
    confidence_percent: number;
    interval_coverage_percent: number;
    avg_actual_confidence_percent: number;
    actual_accuracy_percent: number | null;
    history: PredictionHistoryPoint[];
    predictions: PredictionPoint[];
}

export interface PredictionQuery {
    ticker?: string;
    source: PredictionSource;
    metric?: GoldMetric;
    periods: number;
    intervalWidth?: number;
}

export interface ApiResponse<T> {
    status: string;
    count?: number;
    data: T;
    message?: string;
}

export interface IngestionLogLine {
    id: number;
    timestamp: string;
    message: string;
}

export interface IngestionStatus {
    running: boolean;
    started_at: string | null;
    finished_at: string | null;
    exit_code: number | null;
    last_log_id: number;
}

export interface IngestionLogsResponse {
    lines: IngestionLogLine[];
    next_from_id: number;
    running: boolean;
    started_at: string | null;
    finished_at: string | null;
    exit_code: number | null;
}

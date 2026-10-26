import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, catchError, map, Observable, of, throwError, timeout } from 'rxjs';
import { TimeoutError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { OHLCV, KPI, MonthlyReturn, SMA, Volatility, Drawdown, ApiResponse, KPIStats, IngestionLogsResponse, IngestionStatus, PredictionQuery, PredictionResponse } from '../models/trading.models';

@Injectable({
    providedIn: 'root'
})
export class TradingService {
    private http = inject(HttpClient);
    private apiUrl = environment.apiUrl;
    private defaultTicker = 'AAPL';

    private selectedTickerSubject = new BehaviorSubject<string>(this.defaultTicker);
    selectedTicker$ = this.selectedTickerSubject.asObservable();

    setSelectedTicker(ticker: string) {
        this.selectedTickerSubject.next(ticker);
    }

    getSelectedTicker(): string {
        return this.selectedTickerSubject.getValue();
    }

    getTickers(): Observable<string[]> {
        return this.http.get<{ status: string; tickers: string[] }>(`${this.apiUrl}/ohlcv/tickers`).pipe(
            map(res => res.tickers),
            catchError(() => of([]))
        );
    }

    getOHLCV(ticker: string = this.getSelectedTicker()): Observable<OHLCV[]> {
        return this.http.get<ApiResponse<OHLCV[]>>(`${this.apiUrl}/ohlcv`, { params: { ticker } }).pipe(
            map(res => res.data),
            catchError(() => of([]))
        );
    }

    getKPIs(ticker: string = this.getSelectedTicker()): Observable<any[]> {
        return this.http.get<ApiResponse<any[]>>(`${this.apiUrl}/kpis`, { params: { ticker } }).pipe(
            map(res => res.data),
            catchError(() => of([]))
        );
    }

    getKPIsSummary(ticker: string = this.getSelectedTicker()): Observable<KPIStats | null> {
        return this.http.get<ApiResponse<KPIStats>>(`${this.apiUrl}/kpis/summary`, { params: { ticker } }).pipe(
            map(res => res.data),
            catchError(() => of(null))
        );
    }

    getMonthlyReturns(ticker: string = this.getSelectedTicker()): Observable<MonthlyReturn[]> {
        return this.http.get<ApiResponse<MonthlyReturn[]>>(`${this.apiUrl}/monthly-returns`, { params: { ticker } }).pipe(
            map(res => res.data),
            catchError(() => of([]))
        );
    }

    getSMA(ticker: string = this.getSelectedTicker()): Observable<SMA[]> {
        return this.http.get<ApiResponse<SMA[]>>(`${this.apiUrl}/sma`, { params: { ticker } }).pipe(
            map(res => res.data),
            catchError(() => of([]))
        );
    }

    getVolatility(ticker: string = this.getSelectedTicker()): Observable<Volatility[]> {
        return this.http.get<ApiResponse<Volatility[]>>(`${this.apiUrl}/volatility`, { params: { ticker } }).pipe(
            map(res => res.data),
            catchError(() => of([]))
        );
    }

    getDrawdown(ticker: string = this.getSelectedTicker()): Observable<Drawdown[]> {
        return this.http.get<ApiResponse<Drawdown[]>>(`${this.apiUrl}/drawdown`, { params: { ticker } }).pipe(
            map(res => res.data),
            catchError(() => of([]))
        );
    }

    getPredictions(query: PredictionQuery): Observable<PredictionResponse> {
        const ticker = query.ticker ?? this.getSelectedTicker();
        const params: Record<string, string> = {
            ticker,
            source: query.source,
            periods: String(query.periods),
            interval_width: String(query.intervalWidth ?? 0.95)
        };

        if (query.source === 'gold_metric' && query.metric) {
            params['metric'] = query.metric;
        }

        return this.http.get<ApiResponse<PredictionResponse>>(`${this.apiUrl}/forecast`, { params }).pipe(
            timeout(90000),
            map(res => res.data),
            catchError((error) => {
                if (error instanceof TimeoutError || error?.name === 'TimeoutError') {
                    return throwError(() => ({
                        ...error,
                        message: 'Prediction request timed out after 90s. Try a shorter horizon or retry.'
                    }));
                }
                return throwError(() => error);
            })
        );
    }

    startIngestion(): Observable<{ msg: string; started_at: string }> {
        return this.http.post<{ msg: string; started_at: string }>(`${this.apiUrl}/ingestion/start`, {});
    }

    getIngestionStatus(): Observable<IngestionStatus> {
        return this.http.get<IngestionStatus>(`${this.apiUrl}/ingestion/status`);
    }

    getIngestionLogs(fromId: number): Observable<IngestionLogsResponse> {
        return this.http.get<IngestionLogsResponse>(`${this.apiUrl}/ingestion/logs`, {
            params: { from_id: fromId }
        });
    }
}

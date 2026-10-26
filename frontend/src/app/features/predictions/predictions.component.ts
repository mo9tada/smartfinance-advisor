import { Component, OnDestroy, OnInit, inject, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions } from 'chart.js';
import { Subscription, finalize } from 'rxjs';
import { TradingService } from '../../core/services/trading.service';
import {
    GoldMetric,
    PredictionPoint,
    PredictionResponse,
    PredictionSource,
} from '../../core/models/trading.models';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorCardComponent } from '../../shared/components/error-card/error-card.component';

@Component({
    selector: 'app-predictions',
    standalone: true,
    imports: [CommonModule, FormsModule, BaseChartDirective, LoadingSpinnerComponent, ErrorCardComponent],
    template: `
<div class="space-y-6">
    <app-loading-spinner *ngIf="isLoading()"></app-loading-spinner>
    <app-error-card *ngIf="error()" [message]="error()!" (retry)="runForecast()"></app-error-card>

    <ng-container *ngIf="!error()">
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div class="apple-card p-6 lg:col-span-3">
                <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
                    <div>
                        <h2 class="text-xl font-bold text-[#1d1d1f] tracking-tight">Prophet Forecast</h2>
                        <p class="text-[13px] text-[#86868b] mt-1">
                            Ticker {{ selectedTicker }} with configurable horizon and confidence interval.
                        </p>
                    </div>

                    <button
                        type="button"
                        (click)="runForecast()"
                        [disabled]="isLoading()"
                        class="px-5 py-2 rounded-[10px] text-[13px] font-bold transition-all border"
                        [ngClass]="{
                            'bg-[#e30613] text-white border-[#e30613] hover:bg-[#b8000f]': !isLoading(),
                            'bg-black/10 text-[#86868b] border-black/10 cursor-not-allowed': isLoading()
                        }"
                    >
                        {{ isLoading() ? 'Running...' : 'Run Prediction' }}
                    </button>

                    <button
                        type="button"
                        (click)="resetZoom()"
                        class="px-4 py-2 rounded-[10px] text-[13px] font-bold text-[#e30613] bg-[#e30613]/[0.05] hover:bg-[#e30613]/[0.1] transition-all border border-[#e30613]/10"
                    >
                        Reset Zoom
                    </button>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div class="md:col-span-3">
                        <label class="text-[11px] font-bold uppercase tracking-[0.05em] text-[#86868b] block mb-2">Frequency</label>
                        <div class="inline-flex bg-black/[0.04] rounded-[14px] p-1 border border-black/[0.02] mb-4">
                            <button
                                *ngFor="let f of ['Monthly', 'Yearly']"
                                type="button"
                                (click)="setFrequency(f)"
                                class="px-5 py-2 rounded-[10px] text-[12px] font-semibold transition-all"
                                [class.bg-white]="f === selectedFrequency()"
                                [class.shadow-md]="f === selectedFrequency()"
                                [class.text-[#1d1d1f]]="f === selectedFrequency()"
                                [class.text-[#86868b]]="f !== selectedFrequency()"
                            >
                                {{ f }}
                            </button>
                        </div>
                    </div>

                    <div class="md:col-span-3">
                        <label class="text-[11px] font-bold uppercase tracking-[0.05em] text-[#86868b] block mb-2">Prediction Interval</label>
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                            <label
                                *ngFor="let option of currentHorizonOptions"
                                class="flex items-center gap-2 px-3 py-2 rounded-[10px] border text-[13px] font-medium cursor-pointer transition-colors"
                                [ngClass]="selectedHorizonDays === option.days ? 'border-[#e30613] bg-[#e30613]/[0.06] text-[#1d1d1f]' : 'border-black/10 text-[#1d1d1f] hover:bg-black/[0.03]'"
                            >
                                <input
                                    type="radio"
                                    name="horizon"
                                    [value]="option.days"
                                    [(ngModel)]="selectedHorizonDays"
                                    class="accent-[#e30613]"
                                />
                                <span>{{ option.label }}</span>
                            </label>
                        </div>
                    </div>
                </div>

                <div class="h-[460px]">
                    <canvas baseChart [data]="chartData" [options]="chartOptions" [type]="'line'"></canvas>
                </div>
            </div>

            <div class="space-y-4">
                <div class="apple-card p-6">
                    <p class="text-[11px] font-bold uppercase tracking-[0.05em] text-[#86868b]">Actual Accuracy</p>
                    <p class="text-4xl font-black text-[#1d1d1f] mt-3">{{ actualAccuracyPercent | number:'1.0-2' }}%</p>
                    <p class="text-[12px] text-[#86868b] mt-2">Backtested on holdout historical data.</p>
                </div>

                <div class="apple-card p-6" *ngIf="prediction() as pred">
                    <p class="text-[11px] font-bold uppercase tracking-[0.05em] text-[#86868b]">Request Details</p>
                    <div class="mt-3 space-y-2 text-[13px] text-[#1d1d1f]">
                        <p><span class="text-[#86868b]">Ticker:</span> {{ pred.ticker }}</p>
                        <p><span class="text-[#86868b]">Metric:</span> Close Price</p>
                        <p><span class="text-[#86868b]">Forecast points:</span> {{ pred.predictions.length }}</p>
                    </div>
                </div>
            </div>
        </div>
    </ng-container>
</div>
`
})
export class PredictionsComponent implements OnInit, OnDestroy {
    @ViewChild(BaseChartDirective) chart?: BaseChartDirective;

    private readonly tradingService = inject(TradingService);
    private tickerSubscription?: Subscription;

    isLoading = signal(false);
    error = signal<string | null>(null);
    prediction = signal<PredictionResponse | null>(null);
    selectedFrequency = signal<'Monthly' | 'Yearly'>('Monthly');

    selectedHorizonDays = 30;
    intervalWidth = 0.999;

    readonly monthlyHorizonOptions = [
        { label: 'next month', days: 30 },
        { label: 'next three months', days: 90 },
        { label: 'next six months', days: 180 },
        { label: 'next year', days: 365 }
    ];

    readonly yearlyHorizonOptions = [
        { label: 'next year', days: 365 },
        { label: 'next three years', days: 1095 },
        { label: 'next five years', days: 1825 },
        { label: 'next ten years', days: 3650 }
    ];

    public chartData: ChartConfiguration['data'] = {
        labels: [],
        datasets: [
            {
                data: [],
                label: 'Historical',
                borderColor: '#1d1d1f',
                backgroundColor: 'transparent',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.25
            },
            {
                data: [],
                label: 'Forecast',
                borderColor: '#fb00ff3a',
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [6, 4],
                pointRadius: 0,
                tension: 0.25
            },
            {
                data: [],
                label: 'Upper Bound',
                borderColor: 'rgb(100, 0, 125)',
                borderDash: [4, 4],
                backgroundColor: 'rgba(175, 82, 222, 0.1)',
                borderWidth: 1,
                pointRadius: 0,
                fill: '+1' // Fill down to the next dataset (Lower Bound)
            },
            {
                data: [],
                label: 'Lower Bound',
                borderColor: 'rgb(100, 0, 125)',
                borderDash: [4, 4],
                backgroundColor: 'transparent',
                borderWidth: 1,
                pointRadius: 0,
                fill: false
            }
        ]
    };

    public chartOptions: ChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        normalized: true,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: {
                    color: '#86868b',
                    font: { family: 'Inter', size: 11 },
                    autoSkip: true,
                    maxTicksLimit: 14
                }
            },
            y: {
                grid: { color: 'rgba(0,0,0,0.04)' },
                ticks: {
                    color: '#86868b',
                    font: { family: 'Inter', size: 11 }
                }
            }
        },
        plugins: {
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'xy',
                    threshold: 5,
                },
                zoom: {
                    wheel: {
                        enabled: true,
                        speed: 0.1,
                    },
                    pinch: {
                        enabled: true,
                    },
                    mode: 'xy',
                    drag: {
                        enabled: true,
                        backgroundColor: 'rgba(52, 199, 89, 0.12)',
                        borderColor: 'rgba(52, 199, 89, 0.45)',
                        borderWidth: 1,
                    },
                },
            },
            legend: {
                labels: {
                    usePointStyle: true,
                    color: '#1d1d1f',
                    font: { family: 'Inter', size: 12, weight: 600 }
                }
            },
            decimation: {
                enabled: true,
                algorithm: 'lttb',
                samples: 300
            },
            tooltip: {
                backgroundColor: 'rgba(255, 255, 255, 0.96)',
                titleColor: '#1d1d1f',
                bodyColor: '#1d1d1f',
                borderColor: 'rgba(0,0,0,0.1)',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 12,
                titleFont: { family: 'Inter', size: 13, weight: 700 },
                bodyFont: { family: 'Inter', size: 12 }
            }
        }
    };

    ngOnInit(): void {
        this.tickerSubscription = this.tradingService.selectedTicker$.subscribe(() => {
            this.runForecast();
        });

        this.runForecast();
    }

    ngOnDestroy(): void {
        this.tickerSubscription?.unsubscribe();
    }

    get selectedTicker(): string {
        return this.tradingService.getSelectedTicker();
    }

    get actualConfidencePercent(): number {
        const pred = this.prediction();
        if (!pred) {
            return 0;
        }
        return pred.avg_actual_confidence_percent ?? pred.confidence_percent ?? 0;
    }

    get actualAccuracyPercent(): number {
        const pred = this.prediction();
        if (!pred) {
            return 0;
        }
        return pred.actual_accuracy_percent ?? 0;
    }

    resetZoom(): void {
        this.chart?.chart?.resetZoom();
    }

    setFrequency(value: string): void {
        this.selectedFrequency.set(value as 'Monthly' | 'Yearly');

        const availableDays = this.currentHorizonOptions.map(option => option.days);
        if (!availableDays.includes(this.selectedHorizonDays)) {
            this.selectedHorizonDays = this.currentHorizonOptions[0].days;
        }

        const current = this.prediction();
        if (current) {
            this.renderChart(current);
        }
    }

    get currentHorizonOptions(): Array<{ label: string; days: number }> {
        return this.selectedFrequency() === 'Monthly' ? this.monthlyHorizonOptions : this.yearlyHorizonOptions;
    }

    runForecast(): void {
        this.error.set(null);

        this.intervalWidth = 0.999;

        this.isLoading.set(true);

        this.tradingService.getPredictions({
            ticker: this.selectedTicker,
            source: 'silver_close',
            periods: this.selectedHorizonDays,
            intervalWidth: this.intervalWidth
        }).pipe(
            finalize(() => this.isLoading.set(false))
        ).subscribe({
            next: (response) => {
                this.prediction.set(response);
                this.renderChart(response);
            },
            error: (err) => {
                const message = err?.error?.message || err?.message || 'Failed to run forecast.';
                this.error.set(message);
                this.prediction.set(null);
                this.clearChart();
            }
        });
    }

    private renderChart(response: PredictionResponse): void {
        const { history, forecast } = this.getFrequencyAdjustedData(response);
        const isYearly = this.selectedFrequency() === 'Yearly';

        const historyLabels = history.map(point => this.formatDate(point.date));
        const forecastLabels = forecast.map(point => this.formatDate(point.date));
        const labels = [...historyLabels, ...forecastLabels];

        const historyValues = history.map(point => point.value);
        const paddingBeforeAnchor = new Array(Math.max(history.length - 1, 0)).fill(null);
        const lastHistoryValue = historyValues.length > 0 ? historyValues[historyValues.length - 1] : null;

        const forecastSeries = [
            ...paddingBeforeAnchor,
            lastHistoryValue,
            ...forecast.map((point) => point.yhat)
        ];

        const upperSeries = [
            ...paddingBeforeAnchor,
            lastHistoryValue,
            ...forecast.map((point) => point.yhat_upper)
        ];

        const lowerSeries = [
            ...paddingBeforeAnchor,
            lastHistoryValue,
            ...forecast.map((point) => point.yhat_lower)
        ];

        this.chartData.labels = labels;
        this.chartData.datasets[0].data = [...historyValues, ...new Array(forecast.length).fill(null)];
        this.chartData.datasets[1].data = forecastSeries;
        this.chartData.datasets[2].data = upperSeries;
        this.chartData.datasets[3].data = lowerSeries;

        const historyDataset = this.chartData.datasets[0] as any;
        const forecastDataset = this.chartData.datasets[1] as any;
        historyDataset.pointRadius = isYearly ? 1.5 : 0;
        forecastDataset.pointRadius = isYearly ? 1.5 : 0;
        forecastDataset.borderWidth = isYearly ? 2.5 : 2;

        this.applyDynamicYAxisBounds(
            historyValues,
            forecastSeries,
            lowerSeries,
            upperSeries,
        );

        this.chart?.update('none');
    }

    private getFrequencyAdjustedData(response: PredictionResponse): {
        history: Array<{ date: string; value: number }>;
        forecast: PredictionPoint[];
    } {
        if (this.selectedFrequency() === 'Monthly') {
            return {
                history: this.aggregateHistory(response.history, 'month'),
                forecast: this.aggregateForecast(response.predictions, 'month')
            };
        }

        return {
            history: this.aggregateHistory(response.history, 'year'),
            forecast: this.aggregateForecast(response.predictions, 'year')
        };
    }

    private aggregateHistory(
        points: Array<{ date: string; value: number }>,
        mode: 'month' | 'year'
    ): Array<{ date: string; value: number }> {
        const grouped = new Map<string, { date: string; value: number }>();

        for (const point of points) {
            const date = new Date(point.date);
            const key = mode === 'month'
                ? `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`
                : `${date.getUTCFullYear()}`;

            const existing = grouped.get(key);
            if (!existing || new Date(point.date) > new Date(existing.date)) {
                grouped.set(key, point);
            }
        }

        return Array.from(grouped.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }

    private aggregateForecast(points: PredictionPoint[], mode: 'month' | 'year'): PredictionPoint[] {
        const grouped = new Map<string, PredictionPoint>();

        for (const point of points) {
            const date = new Date(point.date);
            const key = mode === 'month'
                ? `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`
                : `${date.getUTCFullYear()}`;

            const existing = grouped.get(key);
            if (!existing || new Date(point.date) > new Date(existing.date)) {
                grouped.set(key, point);
            }
        }

        return Array.from(grouped.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }

    private clearChart(): void {
        this.chartData.labels = [];
        this.chartData.datasets.forEach(dataset => {
            dataset.data = [];
        });

        const yScale = this.chartOptions.scales?.['y'];
        if (yScale && typeof yScale === 'object') {
            delete (yScale as any).min;
            delete (yScale as any).max;
        }

        this.chart?.update('none');
    }

    private applyDynamicYAxisBounds(
        historySeries: Array<number | null>,
        forecastSeries: Array<number | null>,
        lowerSeries: Array<number | null>,
        upperSeries: Array<number | null>,
    ): void {
        const coreValues = [...historySeries, ...forecastSeries, ...lowerSeries, ...upperSeries]
            .filter((value): value is number => value !== null && Number.isFinite(value));

        if (coreValues.length === 0) {
            return;
        }

        let minValue = Math.min(...coreValues);
        let maxValue = Math.max(...coreValues);

        if (this.selectedFrequency() === 'Yearly' && coreValues.length >= 5) {
            const sortedCore = [...coreValues].sort((a, b) => a - b);
            const q10 = this.getQuantile(sortedCore, 0.1);
            const q90 = this.getQuantile(sortedCore, 0.9);
            minValue = Math.min(minValue, q10);
            maxValue = Math.max(maxValue, q90);
        }

        const range = maxValue - minValue;

        // Keep a visible vertical spread even when values are very close.
        const baselinePadding = Math.max(Math.abs(maxValue), Math.abs(minValue), 1) * 0.05;
        const padding = range > 0 ? range * 0.12 : baselinePadding;

        const yScale = this.chartOptions.scales?.['y'];
        if (!yScale || typeof yScale !== 'object') {
            return;
        }

        (yScale as any).min = minValue - padding;
        (yScale as any).max = maxValue + padding;
    }

    private getQuantile(sortedValues: number[], q: number): number {
        if (sortedValues.length === 0) {
            return 0;
        }

        const clampedQ = Math.min(1, Math.max(0, q));
        const index = (sortedValues.length - 1) * clampedQ;
        const lowerIndex = Math.floor(index);
        const upperIndex = Math.ceil(index);

        if (lowerIndex === upperIndex) {
            return sortedValues[lowerIndex];
        }

        const weight = index - lowerIndex;
        return sortedValues[lowerIndex] * (1 - weight) + sortedValues[upperIndex] * weight;
    }

    private formatDate(value: string): string {
        const date = new Date(value);
        return date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: '2-digit' });
    }

    trackByDate(_: number, point: PredictionPoint): string {
        return point.date;
    }
}

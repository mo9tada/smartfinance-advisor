import { Component, OnInit, inject, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions } from 'chart.js';
import { TradingService } from '../../core/services/trading.service';
import { SMA } from '../../core/models/trading.models';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorCardComponent } from '../../shared/components/error-card/error-card.component';

@Component({
    selector: 'app-price-chart',
    standalone: true,
    imports: [CommonModule, BaseChartDirective, LoadingSpinnerComponent, ErrorCardComponent],
    templateUrl: './price-chart.component.html'
})
export class PriceChartComponent implements OnInit {
    @ViewChild(BaseChartDirective) chart?: BaseChartDirective;
    private tradingService = inject(TradingService);

    isLoading = signal(true);
    error = signal<string | null>(null);

    toggles = {
        close: signal(true),
        sma12: signal(true),
        sma24: signal(true)
    };

    selectedFrequency = signal<'Monthly' | 'Yearly'>('Monthly');

    public chartData: ChartConfiguration['data'] = {
        datasets: [
            {
                data: [],
                label: 'Close',
                borderColor: '#e30613', // Apple Blue
                backgroundColor: 'transparent',
                borderWidth: 3,
                pointRadius: 0
            },
            {
                data: [],
                label: 'SMA 12M',
                borderColor: '#34c759', // Apple Green
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [5, 5],
                pointRadius: 0
            },
            {
                data: [],
                label: 'SMA 24M',
                borderColor: '#ff9500', // Apple Orange
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [2, 2],
                pointRadius: 0
            }
        ],
        labels: []
    };

    public chartOptions: ChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 400
        },
        interaction: {
            mode: 'index',
            intersect: false,
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: {
                    color: '#86868b',
                    font: { family: 'Inter', size: 12 },
                    autoSkip: true,
                    maxTicksLimit: 12
                }
            },
            y: {
                grid: { color: 'rgba(0,0,0,0.03)' },
                ticks: { color: '#86868b', font: { family: 'Inter', size: 12 } }
            }
        },
        plugins: {
            legend: { display: false },
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'xy',
                    threshold: 5
                },
                zoom: {
                    wheel: {
                        enabled: true,
                        speed: 0.1
                    },
                    pinch: {
                        enabled: true
                    },
                    mode: 'xy',
                    drag: {
                        enabled: true,
                        backgroundColor: 'rgba(227, 6, 19, 0.1)',
                        borderColor: 'rgba(227, 6, 19, 0.4)',
                        borderWidth: 1
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                titleColor: '#1d1d1f',
                bodyColor: '#1d1d1f',
                borderColor: 'rgba(0,0,0,0.1)',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 12,
                titleFont: { family: 'Inter', size: 13, weight: 700 },
                bodyFont: { family: 'Inter', size: 13 }
            }
        }
    };

    allData: SMA[] = [];
    selectedRange = signal('All');

    ngOnInit() {
        this.tradingService.selectedTicker$.subscribe(() => {
            this.loadData();
        });
    }

    resetZoom() {
        this.chart?.chart?.resetZoom();
    }

    loadData() {
        this.isLoading.set(true);
        this.error.set(null);
        this.selectedRange.set('All');

        this.tradingService.getSMA().subscribe({
            next: (data) => {
                this.allData = data;
                this.applyFilters();
                this.isLoading.set(false);
            },
            error: () => {
                this.error.set('Failed to load SMA data');
                this.isLoading.set(false);
            }
        });
    }

    setFrequency(freq: string) {
        this.selectedFrequency.set(freq as 'Monthly' | 'Yearly');
        this.applyFilters();
    }

    filterData(range: string) {
        this.selectedRange.set(range);
        this.applyFilters();
    }

    private applyFilters() {
        if (this.allData.length === 0) return;

        let filtered = [...this.allData];
        const range = this.selectedRange();

        if (range !== 'All') {
            const latestDate = new Date(this.allData[this.allData.length - 1].date);
            let startDate = new Date(latestDate);

            if (range === '1Y') startDate.setFullYear(latestDate.getFullYear() - 1);
            else if (range === '3Y') startDate.setFullYear(latestDate.getFullYear() - 3);
            else if (range === '5Y') startDate.setFullYear(latestDate.getFullYear() - 5);

            filtered = this.allData.filter(d => new Date(d.date) >= startDate);
        }

        if (this.selectedFrequency() === 'Yearly') {
            filtered = this.aggregateYearly(filtered);
        }

        this.updateChart(filtered);
    }

    private aggregateYearly(data: SMA[]): SMA[] {
        const yearlyMap = new Map<number, SMA>();
        data.forEach(d => {
            const year = new Date(d.date).getFullYear();
            // Usually we take the last point of the year for price charts
            yearlyMap.set(year, d);
        });
        return Array.from(yearlyMap.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }

    updateChart(data: SMA[]) {
        this.chartData.labels = data.map(d => {
            const date = new Date(d.date);
            if (this.selectedFrequency() === 'Yearly') {
                return date.getFullYear().toString();
            }
            return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
        });

        this.chartData.datasets[0].data = data.map(d => d.close);
        this.chartData.datasets[1].data = data.map(d => d.sma_12);
        this.chartData.datasets[2].data = data.map(d => d.sma_24);
        this.chart?.update();
    }

    toggleSeries(series: 'close' | 'sma12' | 'sma24', index: number) {
        this.toggles[series].update(v => !v);
        if (this.chartData.datasets[index]) {
            this.chartData.datasets[index].hidden = !this.toggles[series]();
            this.chart?.update();
        }
    }
}


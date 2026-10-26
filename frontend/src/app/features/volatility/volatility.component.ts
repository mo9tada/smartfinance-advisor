import { Component, OnInit, inject, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions, ScriptableContext } from 'chart.js';
import { TradingService } from '../../core/services/trading.service';
import { Volatility } from '../../core/models/trading.models';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorCardComponent } from '../../shared/components/error-card/error-card.component';

@Component({
    selector: 'app-volatility',
    standalone: true,
    imports: [CommonModule, BaseChartDirective, LoadingSpinnerComponent, ErrorCardComponent],
    templateUrl: './volatility.component.html'
})
export class VolatilityComponent implements OnInit {
    @ViewChild(BaseChartDirective) chart?: BaseChartDirective;
    private tradingService = inject(TradingService);

    isLoading = signal(true);
    error = signal<string | null>(null);

    public chartData: ChartConfiguration['data'] = {
        datasets: [
            {
                data: [],
                label: 'Volatility',
                borderColor: '#34c759',
                backgroundColor: 'rgba(52, 199, 89, 0.08)',
                fill: true,
                pointRadius: 0,
                borderWidth: 3,
                tension: 0.4
            },
            {
                data: [],
                label: 'Mean',
                borderColor: '#ff9500',
                borderDash: [5, 5],
                pointRadius: 0,
                borderWidth: 2,
                fill: false
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
            legend: {
                display: true,
                position: 'top',
                align: 'end',
                labels: { color: '#1d1d1f', font: { family: 'Inter', size: 12, weight: 600 } }
            },
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
                        backgroundColor: 'rgba(52, 199, 89, 0.1)',
                        borderColor: 'rgba(52, 199, 89, 0.4)',
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

    allData: Volatility[] = [];
    selectedRange = signal('All');
    selectedFrequency = signal<'Monthly' | 'Yearly'>('Monthly');

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

        this.tradingService.getVolatility().subscribe({
            next: (data) => {
                this.allData = data;
                this.applyFilters();
                this.isLoading.set(false);
            },
            error: () => {
                this.error.set('Failed to load volatility data');
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

    private aggregateYearly(data: Volatility[]): Volatility[] {
        const yearlyMap = new Map<number, Volatility>();
        data.forEach(d => {
            const year = new Date(d.date).getFullYear();
            yearlyMap.set(year, d);
        });
        return Array.from(yearlyMap.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }

    updateChart(data: Volatility[]) {
        this.chartData.labels = data.map(d => {
            const date = new Date(d.date);
            if (this.selectedFrequency() === 'Yearly') {
                return date.getFullYear().toString();
            }
            return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
        });

        const values = data.map(d => d.volatility);
        const avg = values.reduce((a, b) => a + b, 0) / values.length;

        this.chartData.datasets[0].data = values;
        this.chartData.datasets[1].data = new Array(data.length).fill(avg);
        this.chart?.update();
    }
}

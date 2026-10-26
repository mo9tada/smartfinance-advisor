import { Component, OnInit, inject, signal, ViewChildren, QueryList } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions } from 'chart.js';
import { TradingService } from '../../core/services/trading.service';
import { Drawdown } from '../../core/models/trading.models';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorCardComponent } from '../../shared/components/error-card/error-card.component';

@Component({
    selector: 'app-drawdown',
    standalone: true,
    imports: [CommonModule, BaseChartDirective, LoadingSpinnerComponent, ErrorCardComponent],
    templateUrl: './drawdown.component.html'
})
export class DrawdownComponent implements OnInit {
    @ViewChildren(BaseChartDirective) charts?: QueryList<BaseChartDirective>;
    private tradingService = inject(TradingService);

    isLoading = signal(true);
    error = signal<string | null>(null);

    // Peak vs Close Chart
    public peakChartData: ChartConfiguration['data'] = {
        datasets: [
            {
                data: [],
                label: 'Peak',
                borderColor: '#34c759',
                backgroundColor: 'transparent',
                pointRadius: 0,
                borderWidth: 2
            },
            {
                data: [],
                label: 'Close',
                borderColor: '#e30613',
                backgroundColor: 'rgba(227, 6, 19, 0.05)',
                fill: true,
                pointRadius: 0,
                borderWidth: 3
            }
        ],
        labels: []
    };

    // Drawdown % Chart
    public ddChartData: ChartConfiguration['data'] = {
        datasets: [
            {
                data: [],
                label: 'Drawdown',
                borderColor: '#ff3b30',
                backgroundColor: 'rgba(255, 59, 48, 0.1)',
                fill: true,
                pointRadius: 0,
                borderWidth: 2
            }
        ],
        labels: []
    };

    public peakChartOptions: ChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        interaction: { mode: 'index', intersect: false },
        scales: {
            x: { grid: { display: false }, ticks: { color: '#86868b', font: { family: 'Inter', size: 12 }, autoSkip: true, maxTicksLimit: 12 } },
            y: { grid: { color: 'rgba(0,0,0,0.03)' }, ticks: { color: '#86868b', font: { family: 'Inter', size: 12 } } }
        },
        plugins: {
            legend: { display: true, position: 'top', align: 'end', labels: { color: '#1d1d1f', font: { family: 'Inter', size: 12, weight: 600 } } },
            zoom: {
                pan: { enabled: true, mode: 'xy', threshold: 5 },
                zoom: {
                    wheel: { enabled: true, speed: 0.1 },
                    pinch: { enabled: true },
                    mode: 'xy',
                    drag: { enabled: true, backgroundColor: 'rgba(227, 6, 19, 0.1)', borderColor: 'rgba(227, 6, 19, 0.4)', borderWidth: 1 }
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

    public ddChartOptions: ChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        interaction: { mode: 'index', intersect: false },
        scales: {
            x: { grid: { display: false }, ticks: { color: '#86868b', font: { family: 'Inter', size: 12 }, autoSkip: true, maxTicksLimit: 12 } },
            y: { grid: { color: 'rgba(0,0,0,0.03)' }, ticks: { color: '#86868b', font: { family: 'Inter', size: 12 }, callback: (v) => v + '%' } }
        },
        plugins: {
            legend: { display: false },
            zoom: {
                pan: { enabled: true, mode: 'xy', threshold: 5 },
                zoom: {
                    wheel: { enabled: true, speed: 0.1 },
                    pinch: { enabled: true },
                    mode: 'xy',
                    drag: { enabled: true, backgroundColor: 'rgba(255, 59, 48, 0.1)', borderColor: 'rgba(255, 59, 48, 0.4)', borderWidth: 1 }
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
                bodyFont: { family: 'Inter', size: 13 },
                callbacks: { label: (c: any) => `Drawdown: ${c.parsed.y.toFixed(2)}%` }
            }
        }
    };

    allData: Drawdown[] = [];
    selectedRange = signal('All');
    selectedFrequency = signal<'Monthly' | 'Yearly'>('Monthly');

    ngOnInit() {
        this.tradingService.selectedTicker$.subscribe(() => {
            this.loadData();
        });
    }

    resetZoom() {
        this.charts?.forEach(chart => chart.chart?.resetZoom());
    }

    loadData() {
        this.isLoading.set(true);
        this.error.set(null);
        this.selectedRange.set('All');

        this.tradingService.getDrawdown().subscribe({
            next: (data) => {
                this.allData = data;
                this.applyFilters();
                this.isLoading.set(false);
            },
            error: () => {
                this.error.set('Failed to load drawdown data');
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

        this.updateCharts(filtered);
    }

    private aggregateYearly(data: Drawdown[]): Drawdown[] {
        const yearlyMap = new Map<number, Drawdown>();
        data.forEach(d => {
            const year = new Date(d.date).getFullYear();
            yearlyMap.set(year, d);
        });
        return Array.from(yearlyMap.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }

    updateCharts(data: Drawdown[]) {
        const labels = data.map(d => {
            const date = new Date(d.date);
            if (this.selectedFrequency() === 'Yearly') {
                return date.getFullYear().toString();
            }
            return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
        });

        this.peakChartData.labels = labels;
        this.peakChartData.datasets[0].data = data.map(d => d.peak);
        this.peakChartData.datasets[1].data = data.map(d => d.close);

        this.ddChartData.labels = labels;
        this.ddChartData.datasets[0].data = data.map(d => d.drawdown * 100); // Percentage

        this.charts?.forEach(chart => chart.update());
    }
}


import { Component, OnInit, inject, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions, ChartType } from 'chart.js';
import { TradingService } from '../../core/services/trading.service';
import { OHLCV, KPI } from '../../core/models/trading.models';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorCardComponent } from '../../shared/components/error-card/error-card.component';
import { forkJoin } from 'rxjs';

@Component({
    selector: 'app-overview',
    standalone: true,
    imports: [CommonModule, BaseChartDirective, LoadingSpinnerComponent, ErrorCardComponent],
    templateUrl: './overview.component.html'
})
export class OverviewComponent implements OnInit {
    @ViewChild(BaseChartDirective) chart?: BaseChartDirective;
    private tradingService = inject(TradingService);

    isLoading = signal(true);
    error = signal<string | null>(null);
    kpis = signal<KPI[]>([]);
    ohlcvData = signal<OHLCV[]>([]);
    selectedRange = signal('All');
    selectedFrequency = signal<'Monthly' | 'Yearly'>('Monthly');

    // Chart Configuration
    public chartData: ChartConfiguration['data'] = {
        datasets: [
            {
                data: [],
                label: 'Price',
                borderColor: '#e30613',
                backgroundColor: 'rgba(227, 6, 19, 0.08)',
                fill: 'origin',
                yAxisID: 'y',
                type: 'line',
                borderWidth: 3,
                pointRadius: 0
            },
            {
                data: [],
                label: 'Volume',
                backgroundColor: 'rgba(227, 6, 19, 0.15)',
                yAxisID: 'y1',
                type: 'bar',
                borderRadius: 4
            }
        ],
        labels: []
    };

    public chartOptions: ChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 400 // Smooth entry animations
        },
        interaction: {
            mode: 'index',
            intersect: false,
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: { color: '#86868b', font: { family: 'Inter', size: 12, weight: 500 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }
            },
            y: {
                position: 'left',
                grid: { color: 'rgba(0,0,0,0.03)' },
                ticks: { color: '#86868b', font: { family: 'Inter', size: 11 } }
            },
            y1: {
                position: 'right',
                grid: { display: false },
                ticks: { display: false }
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

    resetZoom() {
        this.chart?.chart?.resetZoom();
    }

    ngOnInit() {
        this.tradingService.selectedTicker$.subscribe(() => {
            this.loadData();
        });
    }

    loadData() {
        this.isLoading.set(true);
        this.error.set(null);

        forkJoin({
            summary: this.tradingService.getKPIsSummary(),
            ohlcv: this.tradingService.getOHLCV()
        }).subscribe({
            next: (res) => {
                if (res.summary) {
                    this.kpis.set([
                        { kpi_name: 'Avg Return', value: res.summary.avg_return },
                        { kpi_name: 'Avg Volatility', value: res.summary.avg_volatility },
                        { kpi_name: 'Max Drawdown', value: res.summary.max_drawdown },
                        { kpi_name: 'Total Rows', value: res.summary.total_rows }
                    ]);
                }
                this.ohlcvData.set(res.ohlcv);
                this.applyFilters();
                this.isLoading.set(false);
            },
            error: () => {
                this.error.set('Failed to load overview data');
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
        let filtered = [...this.ohlcvData()];
        const range = this.selectedRange();

        if (range !== 'All' && filtered.length > 0) {
            const latestTs = Math.max(...filtered.map(d => new Date(d.date).getTime()));
            const latestDate = new Date(latestTs);
            const years = parseInt(range.replace('Y', ''));
            const cutoff = new Date(latestDate);
            cutoff.setFullYear(latestDate.getFullYear() - years);

            filtered = filtered.filter(d => new Date(d.date) >= cutoff);
        }

        if (this.selectedFrequency() === 'Yearly') {
            filtered = this.aggregateYearly(filtered);
        }

        this.updateChart(filtered);
    }

    private aggregateYearly(data: OHLCV[]): OHLCV[] {
        const yearGroups = new Map<number, OHLCV[]>();
        data.forEach(d => {
            const year = new Date(d.date).getFullYear();
            if (!yearGroups.has(year)) yearGroups.set(year, []);
            yearGroups.get(year)!.push(d);
        });

        return Array.from(yearGroups.keys()).sort().map(year => {
            const group = yearGroups.get(year)!;
            group.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
            
            return {
                date: `${year}-12-31`,
                open_price: group[0].open_price,
                high_price: Math.max(...group.map(x => x.high_price)),
                low_price: Math.min(...group.map(x => x.low_price)),
                close_price: group[group.length - 1].close_price,
                volume: group.reduce((acc, curr) => acc + (curr.volume || 0), 0)
            };
        });
    }

    updateChart(data: OHLCV[]) {
        this.chartData.labels = data.map(d => {
            const date = new Date(d.date);
            if (this.selectedFrequency() === 'Yearly') {
                return date.getFullYear().toString();
            }
            return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
        });
        this.chartData.datasets[0].data = data.map(d => d.close_price);
        this.chartData.datasets[1].data = data.map(d => d.volume);
        this.chart?.update();
    }

}


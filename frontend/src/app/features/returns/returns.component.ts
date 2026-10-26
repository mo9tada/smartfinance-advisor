import { Component, OnInit, inject, signal, computed, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions, ScriptableContext } from 'chart.js';
import { TradingService } from '../../core/services/trading.service';
import { MonthlyReturn } from '../../core/models/trading.models';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ErrorCardComponent } from '../../shared/components/error-card/error-card.component';

@Component({
    selector: 'app-returns',
    standalone: true,
    imports: [CommonModule, BaseChartDirective, LoadingSpinnerComponent, ErrorCardComponent],
    templateUrl: './returns.component.html'
})
export class ReturnsComponent implements OnInit {
    @ViewChild(BaseChartDirective) chart?: BaseChartDirective;
    private tradingService = inject(TradingService);

    isLoading = signal(true);
    error = signal<string | null>(null);
    returnsData = signal<MonthlyReturn[]>([]);
    allData: MonthlyReturn[] = [];
    selectedRange = signal('All');
    selectedFrequency = signal<'Monthly' | 'Yearly'>('Monthly');

    stats = computed(() => {
        const data = this.returnsData();
        if (data.length === 0) return null;

        const values = data.map(d => d.monthly_return).filter(v => v !== null) as number[];
        if (values.length === 0) return null;

        return {
            best: Math.max(...values),
            worst: Math.min(...values),
            average: values.reduce((a, b) => a + b, 0) / values.length
        };
    });

    public chartData: ChartConfiguration['data'] = {
        datasets: [
            {
                data: [],
                label: 'Monthly Return',
                backgroundColor: (context: ScriptableContext<'bar'>) => {
                    const value = context.raw as number;
                    // Absolute solid primary colors to combat anti-aliasing fade
                    return value >= 0 ? '#10b981' : '#ef4444';
                },
                hoverBackgroundColor: (context: ScriptableContext<'bar'>) => {
                    const value = context.raw as number;
                    return value >= 0 ? '#059669' : '#b91c1c';
                },
                borderColor: (context: ScriptableContext<'bar'>) => {
                    const value = context.raw as number;
                    return value >= 0 ? '#249d3d' : '#e02d1b';
                },
                borderWidth: 0,
                borderRadius: 0,
                categoryPercentage: 1.0,
                barPercentage: 1.0,
                minBarLength: 2
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
                    font: { family: 'Inter', size: 12, weight: 500 },
                    maxRotation: 0,
                    autoSkip: true,
                    maxTicksLimit: 10
                }
            },
            y: {
                grid: {
                    color: (context) => context.tick.value === 0 ? 'rgba(0,0,0,0.2)' : 'rgba(0,0,0,0.03)',
                    lineWidth: (context) => context.tick.value === 0 ? 2 : 1
                },
                ticks: {
                    color: '#86868b',
                    font: { family: 'Inter', size: 11 },
                    callback: (value) => value + '%'
                }
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
                bodyFont: { family: 'Inter', size: 13 },
                callbacks: {
                    label: (context: any) => `Return: ${context.parsed.y?.toFixed(2) ?? '0.00'}%`
                }
            }
        },
        elements: {
            bar: {
                borderRadius: 0,
                borderWidth: 0
            }
        }
    };

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

        this.tradingService.getMonthlyReturns().subscribe({
            next: (data) => {
                this.allData = data;
                this.applyFilters();
                this.isLoading.set(false);
            },
            error: () => {
                this.error.set('Failed to load returns data');
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

        this.returnsData.set(filtered);
        this.updateChart(filtered);
    }

    private aggregateYearly(data: MonthlyReturn[]): MonthlyReturn[] {
        const yearGroups = new Map<number, MonthlyReturn[]>();
        data.forEach(d => {
            const dateObj = new Date(d.date);
            const year = dateObj.getFullYear();
            if (!yearGroups.has(year)) yearGroups.set(year, []);
            yearGroups.get(year)!.push(d);
        });

        return Array.from(yearGroups.keys()).sort().map(year => {
            const group = yearGroups.get(year)!;
            // Sort group by date to ensure we have the correct last price
            group.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
            
            // Compound returns: (1+r1)*(1+r2)... - 1
            const compounded = group.reduce((acc, curr) => acc * (1 + (curr.monthly_return || 0) / 100), 1) - 1;
            
            return {
                date: `${year}-12-31`,
                monthly_return: compounded * 100,
                close_price: group[group.length - 1].close_price
            };
        });
    }

    updateChart(data: MonthlyReturn[]) {
        if (!this.chartData.datasets[0]) return;

        this.chartData.labels = data.map(d => {
            const date = new Date(d.date);
            if (this.selectedFrequency() === 'Yearly') {
                return date.getFullYear().toString();
            }
            return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
        });

        this.chartData.datasets[0].data = data.map(d => d.monthly_return);

        // Adjust bar density based on data volume
        const dataset = this.chartData.datasets[0] as any;
        if (dataset.barPercentage !== undefined) {
            dataset.barPercentage = data.length > 50 ? 1.0 : 0.8;
            dataset.categoryPercentage = data.length > 50 ? 1.0 : 0.8;
        }

        this.chart?.update();
    }
}


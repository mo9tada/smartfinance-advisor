import { Component, Input, Output, EventEmitter, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TradingService } from '../../core/services/trading.service';
import { AuthService } from '../../core/services/auth.service';
import { IngestionLogLine } from '../../core/models/trading.models';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  template: `
    <div [class.w-72]="!isCollapsed" 
         [class.w-20]="isCollapsed"
         [class.-translate-x-full]="isCollapsed && isMobile"
         class="h-screen bg-[#f5f5f7]/80 backdrop-blur-2xl border-r border-black/5 sidebar-transition flex flex-col fixed left-0 top-0 z-50 lg:translate-x-0">
      
      <div class="p-8 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-10 h-10 bg-black rounded-[12px] flex items-center justify-center shadow-lg shrink-0">
            <svg viewBox="0 0 24 24" class="w-6 h-6 text-white" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span *ngIf="!isCollapsed" class="font-bold text-[20px] tracking-tight text-[#1d1d1f]">Advisor</span>
        </div>
        <button *ngIf="isMobile" (click)="toggleCollapse.emit()" class="text-[#86868b] p-2 hover:bg-black/[0.03] rounded-full">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
      </div>

      <!-- Searchable Ticker Selector -->
      <div *ngIf="!isCollapsed" class="px-6 mb-8 relative">
        <div class="bg-black/[0.03] rounded-2xl p-4 border border-black/5 transition-all hover:bg-black/[0.05]">
          <label class="text-[10px] font-bold text-[#86868b] uppercase tracking-[0.05em] mb-2 block ml-1">Market Scope</label>
          
          <div class="relative group">
            <input type="text" 
                   [(ngModel)]="searchQuery" 
                   (focus)="showDropdown = true"
                   placeholder="Search Tickers..."
                   class="w-full bg-transparent text-[14px] font-semibold text-[#1d1d1f] py-1 placeholder:text-[#86868b] focus:outline-none">
            
            <div class="absolute right-0 top-1/2 -translate-y-1/2 text-[#86868b] transition-transform group-focus-within:rotate-180">
              <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/></svg>
            </div>
          </div>
        </div>

        <!-- Custom Dropdown List -->
        <div *ngIf="showDropdown" 
             class="absolute left-6 right-6 top-full mt-2 bg-white/90 backdrop-blur-xl border border-black/5 rounded-2xl shadow-2xl z-[60] py-2 max-h-64 overflow-y-auto custom-scrollbar animate-fade-in">
          <div *ngFor="let ticker of filteredTickers" 
               (click)="selectTicker(ticker)"
               class="px-4 py-2.5 hover:bg-[#e30613] hover:text-white cursor-pointer transition-colors flex items-center justify-between group">
            <span class="font-semibold text-sm">{{ ticker }}</span>
            <span *ngIf="ticker === selectedTicker" class="text-blue-500 group-hover:text-white scale-75">
              <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>
            </span>
          </div>
          <div *ngIf="filteredTickers.length === 0" class="px-4 py-4 text-center text-[#86868b] text-xs font-medium">
            No tickers found
          </div>
        </div>
      </div>

      <!-- Compact Ticker Icon for collapsed state -->
      <div *ngIf="isCollapsed" class="px-4 mb-8 flex justify-center">
        <div (click)="toggleCollapse.emit()" 
             class="w-12 h-12 rounded-[14px] bg-white border border-black/5 flex items-center justify-center text-[#e30613] font-bold text-[11px] shadow-sm cursor-pointer hover:bg-black/[0.02] transition-all"
             [title]="selectedTicker">
          {{ selectedTicker }}
        </div>
      </div>

      <!-- Backdrop for closing dropdown -->
      <div *ngIf="showDropdown" class="fixed inset-0 z-[55]" (click)="showDropdown = false"></div>

      <nav class="flex-1 px-4 space-y-1 overflow-y-auto custom-scrollbar">
        <a *ngFor="let item of navItems" 
           [routerLink]="item.path"
           routerLinkActive="bg-white shadow-sm text-[#e30613] active"
           class="flex items-center gap-4 p-3.5 rounded-xl text-[#1d1d1f] hover:bg-white/50 group transition-colors">
           <div class="w-8 h-8 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
             <img [src]="item.icon" class="w-5 h-5 grayscale group-[.active]:grayscale-0" [alt]="item.label">
           </div>
           <span *ngIf="!isCollapsed" class="font-medium text-[14px]">{{ item.label }}</span>
        </a>

        <!-- Ask Lexa Button -->
        <a routerLink="/analyst/chat"
           class="mt-4 flex items-center gap-4 p-3.5 rounded-xl text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:shadow-lg group transition-all">
           <div class="w-8 h-8 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300 bg-white/20">
             <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
             </svg>
           </div>
           <span *ngIf="!isCollapsed" class="font-bold text-[14px]">Ask Lexa</span>
        </a>

        <!-- Admin Only Section -->
        <div *ngIf="authService.isAdmin()" class="pt-4 mt-4 border-t border-black/5">
          <p *ngIf="!isCollapsed" class="px-4 text-[10px] font-bold text-[#86868b] uppercase tracking-widest mb-2">Management</p>
          <a routerLink="/admin"
             routerLinkActive="bg-white shadow-sm text-[#e30613] active"
             class="flex items-center gap-4 p-3.5 rounded-xl text-[#1d1d1f] hover:bg-white/50 group transition-colors">
             <div class="w-8 h-8 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
               <svg class="w-5 h-5 text-[#86868b] group-[.active]:text-[#e30613]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path d="M12 4.354l1.1 1.1a1 1 0 001.414 0L16.207 4a1 1 0 011.414 0l.707.707a1 1 0 010 1.414l-1.1 1.1a1 1 0 000 1.414l1.1 1.1a1 1 0 010 1.414l-.707.707a1 1 0 01-1.414 0l-1.1-1.1a1 1 0 00-1.414 0l-1.1 1.1a1 1 0 01-1.414 0l-.707-.707a1 1 0 010-1.414l1.1-1.1a1 1 0 000-1.414l-1.1-1.1a1 1 0 010-1.414l.707-.707a1 1 0 011.414 0l1.1 1.1z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                 <path d="M12 11v10M8 21h8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
               </svg>
             </div>
             <span *ngIf="!isCollapsed" class="font-medium text-[14px]">Administration</span>
          </a>

          <button
            type="button"
            (click)="openIngestionModal()"
            class="w-full mt-2 flex items-center gap-4 p-3.5 rounded-xl text-[#1d1d1f] hover:bg-white/50 group transition-colors"
          >
            <div class="w-8 h-8 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <svg class="w-5 h-5 text-[#86868b] group-hover:text-[#e30613]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M4 7h16M7 12h10M10 17h4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <span *ngIf="!isCollapsed" class="font-medium text-[14px]">Ingest Data</span>
          </button>

          <a
            routerLink="/admin/law-ingestion"
            class="w-full mt-2 flex items-center gap-4 p-3.5 rounded-xl text-[#1d1d1f] hover:bg-white/50 group transition-colors"
          >
            <div class="w-8 h-8 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <svg class="w-5 h-5 text-[#86868b] group-hover:text-[#e30613]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M4 7h16M7 12h10M10 17h4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <span *ngIf="!isCollapsed" class="font-medium text-[14px]">Ingest Laws</span>
          </a>
        </div>
      </nav>

      <button (click)="toggleCollapse.emit()" 
              class="m-6 p-4 rounded-2xl hover:bg-white/80 transition-all flex items-center justify-center border border-black/[0.02] shadow-sm bg-white/30">
        <svg [class.rotate-180]="isCollapsed" class="w-5 h-5 text-[#86868b] transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>
    </div>

    <div
      *ngIf="showIngestionModal"
      class="fixed inset-0 z-[90] bg-black/40 backdrop-blur-[1px] flex items-center justify-center p-4"
      (click)="closeIngestionModal()"
    >
      <div
        class="w-full max-w-3xl bg-white rounded-2xl shadow-2xl border border-black/10 overflow-hidden"
        (click)="$event.stopPropagation()"
      >
        <div class="px-6 py-4 border-b border-black/10 flex items-center justify-between">
          <div>
            <h3 class="text-lg font-bold text-[#1d1d1f]">Data Ingestion</h3>
            <p class="text-[12px] text-[#86868b] mt-1">Runs backend/data_pipeline/main.py and streams logs in realtime.</p>
          </div>
          <button type="button" (click)="closeIngestionModal()" class="p-2 rounded-full hover:bg-black/5 text-[#86868b]">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
        </div>

        <div class="px-6 py-4 space-y-3">
          <div class="flex items-center gap-3">
            <button
              type="button"
              (click)="startIngestion()"
              [disabled]="isIngesting"
              class="px-4 py-2 rounded-[10px] text-[13px] font-bold transition-all border"
              [ngClass]="{
                'bg-[#e30613] text-white border-[#e30613] hover:bg-[#b8000f]': !isIngesting,
                'bg-black/10 text-[#86868b] border-black/10 cursor-not-allowed': isIngesting
              }"
            >
              {{ isIngesting ? 'Ingestion Running...' : 'Start Ingestion' }}
            </button>
            <p class="text-[12px] text-[#86868b]" *ngIf="ingestionExitCode !== null && !isIngesting">
              Last exit code: {{ ingestionExitCode }}
            </p>
          </div>

          <p *ngIf="ingestionError" class="text-[13px] text-red-600 font-medium">{{ ingestionError }}</p>

          <div class="rounded-xl border border-black/10 bg-[#0b1020] p-4 h-72 overflow-auto">
            <div *ngIf="ingestionLogs.length === 0" class="text-[12px] text-white/60 font-mono">
              No logs yet. Click "Start Ingestion" to run the pipeline.
            </div>
            <div *ngFor="let line of ingestionLogs" class="text-[12px] text-white/85 font-mono leading-5">
              [{{ line.timestamp }}] {{ line.message }}
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class SidebarComponent implements OnInit, OnDestroy {
  @Input() isCollapsed = false;
  @Output() toggleCollapse = new EventEmitter<void>();

  private tradingService = inject(TradingService);
  public authService = inject(AuthService);
  isMobile = false;

  searchQuery = '';
  showDropdown = false;
  selectedTicker = '';
  availableTickers: string[] = [];
  showIngestionModal = false;
  isIngesting = false;
  ingestionError: string | null = null;
  ingestionLogs: IngestionLogLine[] = [];
  ingestionExitCode: number | null = null;

  private ingestionPollTimer: ReturnType<typeof setInterval> | null = null;
  private lastIngestionLogId = 0;

  get filteredTickers() {
    return this.availableTickers.filter(t =>
      t.toLowerCase().includes(this.searchQuery.toLowerCase())
    );
  }

  navItems = [
    { label: 'Overview', path: '/dashboard/overview', icon: 'assets/icons/overview.png' },
    { label: 'Price Chart', path: '/dashboard/price-chart', icon: 'assets/icons/price_chart.png' },
    { label: 'Monthly Returns', path: '/dashboard/returns', icon: 'assets/icons/monthly_return.png' },
    { label: 'Volatility', path: '/dashboard/volatility', icon: 'assets/icons/volatility.png' },
    { label: 'Drawdown', path: '/dashboard/drawdown', icon: 'assets/icons/drawdown.png' },
    { label: 'Predictions', path: '/dashboard/predictions', icon: 'assets/icons/price_chart.png' }
  ];

  ngOnInit() {
    this.checkScreenSize();
    window.addEventListener('resize', () => this.checkScreenSize());

    this.selectedTicker = this.tradingService.getSelectedTicker();
    this.searchQuery = this.selectedTicker;

    this.tradingService.getTickers().subscribe(tickers => this.availableTickers = tickers);
    this.tradingService.selectedTicker$.subscribe(ticker => {
      this.selectedTicker = ticker;
      this.searchQuery = ticker;
    });
  }

  ngOnDestroy() {
    this.stopIngestionPolling();
  }

  checkScreenSize() {
    const wasMobile = this.isMobile;
    this.isMobile = window.innerWidth < 1024;

    // Auto-collapse when entering mobile, or expand when entering desktop
    if (this.isMobile && !wasMobile && !this.isCollapsed) {
      this.toggleCollapse.emit();
    } else if (!this.isMobile && wasMobile && this.isCollapsed) {
      this.toggleCollapse.emit();
    }
  }

  selectTicker(ticker: string) {
    this.selectedTicker = ticker;
    this.searchQuery = ticker;
    this.showDropdown = false;
    this.tradingService.setSelectedTicker(ticker);
    if (this.isMobile) this.toggleCollapse.emit();
  }

  onTickerChange(ticker: string) {
    this.tradingService.setSelectedTicker(ticker);
    if (this.isMobile) this.toggleCollapse.emit(); // Auto-close on mobile after selection
  }

  openIngestionModal() {
    if (!this.authService.isAdmin()) {
      return;
    }

    this.showIngestionModal = true;
    this.ingestionError = null;
    this.ingestionLogs = [];
    this.lastIngestionLogId = 0;
    this.bootstrapIngestionState();
  }

  closeIngestionModal() {
    this.showIngestionModal = false;
    this.stopIngestionPolling();
  }

  startIngestion() {
    if (!this.authService.isAdmin() || this.isIngesting) {
      return;
    }

    this.ingestionError = null;
    this.ingestionLogs = [];
    this.lastIngestionLogId = 0;
    this.ingestionExitCode = null;

    this.tradingService.startIngestion().subscribe({
      next: () => {
        this.isIngesting = true;
        this.startIngestionPolling();
      },
      error: (err) => {
        if (err?.status === 403) {
          this.ingestionError = 'Administrator access required.';
          return;
        }
        this.ingestionError = err?.error?.msg || 'Failed to start ingestion.';
      }
    });
  }

  private bootstrapIngestionState() {
    this.tradingService.getIngestionStatus().subscribe({
      next: (status) => {
        this.isIngesting = status.running;
        this.ingestionExitCode = status.exit_code;
        this.fetchIngestionLogs();

        if (status.running) {
          this.startIngestionPolling();
        }
      },
      error: (err) => {
        if (err?.status === 403) {
          this.ingestionError = 'Administrator access required.';
          return;
        }
        this.ingestionError = 'Could not load ingestion status.';
      }
    });
  }

  private startIngestionPolling() {
    this.stopIngestionPolling();
    this.fetchIngestionLogs();

    this.ingestionPollTimer = setInterval(() => {
      this.fetchIngestionLogs();
    }, 1200);
  }

  private stopIngestionPolling() {
    if (this.ingestionPollTimer) {
      clearInterval(this.ingestionPollTimer);
      this.ingestionPollTimer = null;
    }
  }

  private fetchIngestionLogs() {
    this.tradingService.getIngestionLogs(this.lastIngestionLogId).subscribe({
      next: (res) => {
        if (res.lines.length) {
          this.ingestionLogs = [...this.ingestionLogs, ...res.lines];
          this.lastIngestionLogId = res.next_from_id;
        }

        this.isIngesting = res.running;
        this.ingestionExitCode = res.exit_code;

        if (!res.running) {
          this.stopIngestionPolling();
        }
      },
      error: (err) => {
        this.stopIngestionPolling();
        this.isIngesting = false;

        if (err?.status === 403) {
          this.ingestionError = 'Administrator access required.';
          return;
        }

        this.ingestionError = err?.error?.msg || 'Failed to fetch ingestion logs.';
      }
    });
  }
}


import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { TopbarComponent } from '../topbar/topbar.component';
import { filter, map } from 'rxjs';

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent, TopbarComponent],
  template: `
    <div class="min-h-screen flex bg-slate-50 text-slate-900 overflow-hidden">
      <app-sidebar 
        [isCollapsed]="isSidebarCollapsed()" 
        (toggleCollapse)="toggleSidebar()">
      </app-sidebar>

      <main [class.ml-72]="!isSidebarCollapsed()" [class.ml-20]="isSidebarCollapsed()" 
            class="flex-1 transition-all duration-300 h-screen overflow-y-auto bg-[#f5f5f7]">
        <app-topbar [title]="currentPageTitle()"></app-topbar>
        <div class="p-8">
          <router-outlet></router-outlet>
        </div>
      </main>
    </div>
  `,
  styles: [`
    :host { display: block; }
  `]
})
export class DashboardLayoutComponent {
  isSidebarCollapsed = signal(false);
  currentPageTitle = signal('Overview');

  constructor(private router: Router) {
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd),
      map(event => (event as NavigationEnd).urlAfterRedirects)
    ).subscribe(url => {
      this.currentPageTitle.set(this.getTitleFromUrl(url));
    });
    
    // Initial title
    this.currentPageTitle.set(this.getTitleFromUrl(this.router.url));
  }

  toggleSidebar() {
    this.isSidebarCollapsed.update(v => !v);
  }

  private getTitleFromUrl(url: string): string {
    if (url.includes('price-chart')) return 'Price Chart';
    if (url.includes('returns')) return 'Monthly Returns';
    if (url.includes('volatility')) return 'Volatility';
    if (url.includes('drawdown')) return 'Drawdown';
    if (url.includes('admin')) return 'Administration';
    return 'Overview';
  }
}

import { Component, Input, inject, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { toSignal } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="h-20 bg-[#f5f5f7]/60 backdrop-blur-xl px-12 flex items-center justify-between sticky top-0 z-40">
      <h1 class="text-2xl font-bold tracking-tight text-[#1d1d1f]">{{ title }}</h1>
      
      <div class="flex items-center gap-8">
        <div class="text-[13px] font-medium text-[#86868b]">
          Updated: <span class="text-[#1d1d1f] ml-1">{{ lastRefresh | date:'HH:mm:ss' }}</span>
        </div>

        <div class="relative">
          <button (click)="toggleNotifications()" class="relative p-2 text-[#86868b] hover:text-[#1d1d1f] transition-colors rounded-full hover:bg-black/5 focus:outline-none">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
            <span *ngIf="unreadCount() > 0" class="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          <div *ngIf="showNotifications()" class="absolute right-0 mt-2 w-80 bg-white/90 backdrop-blur-xl rounded-2xl shadow-lg border border-black/5 overflow-hidden z-50">
            <div class="p-4 border-b border-black/5 flex justify-between items-center bg-white/50">
              <h3 class="text-sm font-semibold text-[#1d1d1f]">Notifications</h3>
              <span class="text-xs text-[#86868b] bg-black/5 px-2 py-0.5 rounded-full">{{ unreadCount() }} unread</span>
            </div>
            <div class="max-h-80 overflow-y-auto">
              <div *ngIf="notifications()?.length === 0" class="p-8 text-center text-sm text-[#86868b]">
                No notifications right now
              </div>
              <div *ngFor="let n of notifications()" 
                   class="p-4 border-b border-black/5 hover:bg-black/[0.02] transition-colors flex items-start gap-3 cursor-pointer"
                   [ngClass]="{'bg-blue-50/50': !n.is_read}"
                   (click)="markAsRead(n)">
                <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-500 flex items-center justify-center shrink-0 mt-0.5">
                  <svg *ngIf="n.type === 'ingestion'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                  <svg *ngIf="n.type === 'prediction'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                  <svg *ngIf="n.type !== 'ingestion' && n.type !== 'prediction'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-[#1d1d1f]" [class.font-medium]="!n.is_read">{{ n.message }}</p>
                  <p class="text-[11px] text-[#86868b] mt-1">{{ n.created_at | date:'short' }}</p>
                </div>
                <div *ngIf="!n.is_read" class="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3 bg-white/50 py-1.5 px-3 rounded-full border border-black/[0.03] shadow-sm">
          <div class="w-6 h-6 rounded-full bg-gradient-to-tr from-blue-500 to-blue-400 flex items-center justify-center text-[10px] text-white font-bold shadow-sm cursor-default" [title]="user()?.email">
            {{ initials() }}
          </div>
          <span class="text-[13px] font-semibold text-[#1d1d1f]">{{ user()?.full_name || 'User' }}</span>
          <button (click)="authService.logout()" class="ml-2 text-[#86868b] hover:text-red-500 transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
      </div>
    </header>
  `
})
export class TopbarComponent {
  @Input() title = 'Dashboard';
  lastRefresh = new Date();
  authService = inject(AuthService);
  notificationService = inject(NotificationService);

  user = computed(() => this.authService.currentUser());
  notifications = toSignal(this.notificationService.notifications$, { initialValue: [] });
  unreadCount = computed(() => this.notifications().filter(n => !n.is_read).length);
  showNotifications = signal(false);

  initials = computed(() => {
    const name = this.user()?.full_name || 'U';
    return name.split(' ').map((n: string) => n[0]).join('').toUpperCase().substring(0, 2);
  });

  toggleNotifications() {
    this.showNotifications.update(v => !v);
  }

  markAsRead(notification: any) {
    if (!notification.is_read) {
      this.notificationService.markAsRead(notification.id).subscribe(() => {
        this.notificationService.refreshNotifications();
      });
    }
  }
}

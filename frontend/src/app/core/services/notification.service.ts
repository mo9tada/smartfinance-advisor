import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { BehaviorSubject, Observable, interval, switchMap, startWith } from 'rxjs';

export interface Notification {
  id: number;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  private notificationsSubject = new BehaviorSubject<Notification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();

  constructor() {
    this.startPolling();
  }

  private startPolling() {
    // Poll every 30 seconds
    interval(30000)
      .pipe(
        startWith(0),
        switchMap(() => this.http.get<Notification[]>(`${this.apiUrl}/notifications/`))
      )
      .subscribe({
        next: (notifications) => this.notificationsSubject.next(notifications),
        error: (err) => console.error('Failed to fetch notifications', err)
      });
  }

  refreshNotifications() {
    this.http.get<Notification[]>(`${this.apiUrl}/notifications/`).subscribe({
      next: (notifications) => this.notificationsSubject.next(notifications)
    });
  }

  markAsRead(id: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/notifications/${id}/read`, {});
  }
}

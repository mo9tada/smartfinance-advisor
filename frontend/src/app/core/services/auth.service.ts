import { inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, catchError, map, Observable, of, tap, timeout } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User, LoginCredentials, RegisterData, AuthResponse } from '../models/auth.models';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);
  private apiUrl = `${environment.apiUrl}/auth`;

  private currentUserSubject = new BehaviorSubject<User | null>(null);
  currentUser$ = this.currentUserSubject.asObservable();
  currentUser = signal<User | null>(null);
  
  // Expose signals for easier template usage if needed
  isLoggedIn = signal(false);
  isAdmin = signal(false);

  constructor() {
    this.checkSession();
  }

  private checkSession() {
    const token = localStorage.getItem('sfa_token');
    if (token) {
      this.getCurrentUser().subscribe();
    }
  }

  register(data: RegisterData): Observable<any> {
    return this.http.post(`${this.apiUrl}/register`, data);
  }

  login(credentials: LoginCredentials): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials).pipe(
      timeout(15000),
      tap(res => {
        localStorage.setItem('sfa_token', res.access_token);
        this.updateState(res.user);
      })
    );
  }

  logout() {
    localStorage.removeItem('sfa_token');
    this.currentUserSubject.next(null);
    this.isLoggedIn.set(false);
    this.isAdmin.set(false);
    this.router.navigate(['/login']);
  }

  getCurrentUser(): Observable<User | null> {
    return this.http.get<{user: User}>(`${this.apiUrl}/me`).pipe(
      map(res => res.user),
      tap(user => this.updateState(user)),
      catchError(() => {
        this.logout();
        return of(null);
      })
    );
  }

  private updateState(user: User | null) {
    this.currentUserSubject.next(user);
    this.currentUser.set(user);
    this.isLoggedIn.set(!!user);
    this.isAdmin.set(user?.role === 'administrator');
  }

  forgotPassword(email: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/forgot-password`, { email });
  }

  verifyCode(email: string, code: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/verify-reset-code`, { email, code });
  }

  resetPassword(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/reset-password`, data);
  }
}

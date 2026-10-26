import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/admin`;

  getPendingUsers(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/users/pending`);
  }

  acceptUser(id: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/users/accept/${id}`, {});
  }

  rejectUser(id: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/users/reject/${id}`, {});
  }

  getActiveUsers(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/users/active`);
  }

  updateUser(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/users/${id}`, data);
  }

  deleteUser(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/users/${id}`);
  }
}

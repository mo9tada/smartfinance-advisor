import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { IngestionLogsResponse, IngestionStatus } from '../models/trading.models';

@Injectable({
  providedIn: 'root'
})
export class LawIngestionService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/law-ingestion`;

  startIngestion(): Observable<{ msg: string; started_at: string }>{
    return this.http.post<{ msg: string; started_at: string }>(`${this.apiUrl}/start`, {});
  }

  getStatus(): Observable<IngestionStatus> {
    return this.http.get<IngestionStatus>(`${this.apiUrl}/status`);
  }

  getLogs(fromId: number): Observable<IngestionLogsResponse> {
    return this.http.get<IngestionLogsResponse>(`${this.apiUrl}/logs`, {
      params: { from_id: fromId }
    });
  }
}

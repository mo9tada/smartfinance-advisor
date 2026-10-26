import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ChatRequest {
  mode: 'analyst' | 'finance';
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  sources?: string[];
  error?: string;
  session_id?: string;
}

export interface ChatSessionDto {
  id: string;
  title: string;
  mode: 'analyst' | 'finance';
  created_at: string | null;
  updated_at: string | null;
}

export interface ChatMessageDto {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  created_at?: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/chat`;

  listSessions(mode: 'analyst' | 'finance'): Observable<ChatSessionDto[]> {
    return this.http.get<ChatSessionDto[]>(`${this.apiUrl}/sessions`, { params: { mode } });
  }

  createSession(mode: 'analyst' | 'finance', title: string = 'New Chat'): Observable<ChatSessionDto> {
    return this.http.post<ChatSessionDto>(`${this.apiUrl}/sessions`, { mode, title });
  }

  renameSession(sessionId: string, title: string): Observable<ChatSessionDto> {
    return this.http.patch<ChatSessionDto>(`${this.apiUrl}/sessions/${sessionId}`, { title });
  }

  deleteSession(sessionId: string): Observable<{ msg: string }> {
    return this.http.delete<{ msg: string }>(`${this.apiUrl}/sessions/${sessionId}`);
  }

  getMessages(sessionId: string): Observable<ChatMessageDto[]> {
    return this.http.get<ChatMessageDto[]>(`${this.apiUrl}/sessions/${sessionId}/messages`);
  }

  sendMessage(mode: 'analyst' | 'finance', message: string, sessionId?: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/message`, { mode, message, session_id: sessionId });
  }
}

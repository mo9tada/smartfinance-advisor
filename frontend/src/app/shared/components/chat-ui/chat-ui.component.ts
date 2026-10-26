import { Component, Input, OnInit, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ChatService, ChatMessageDto, ChatSessionDto } from '../../../core/services/chat.service';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  isLoading?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  date: Date;
  mode: 'analyst' | 'finance';
}

@Component({
  selector: 'app-chat-ui',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-ui.component.html',
  styleUrl: './chat-ui.component.css'
})
export class ChatUiComponent implements OnInit {
  @Input() mode: 'analyst' | 'finance' = 'analyst';
  @ViewChild('messageList') messageList?: ElementRef<HTMLDivElement>;
  
  private router = inject(Router);
  public authService = inject(AuthService);
  private chatService = inject(ChatService);

  userInput: string = '';
  messages: ChatMessage[] = [];
  sessions: ChatSession[] = [];
  currentSessionId: string | null = null;

  suggestedPrompts: string[] = [];

  ngOnInit() {
    this.suggestedPrompts = this.mode === 'analyst' 
      ? ['Summarize the monthly returns', 'Any anomalies in recent volatility?', 'Generate an Executive Report']
      : ['What is the corporate tax rate in Tunisia?', 'How does VAT work for tech services?', 'Explain fiscal penalties for late filing'];

    this.loadSessions();
  }

  goBack() {
    const route = this.mode === 'analyst' ? '/dashboard' : '/finance';
    this.router.navigate([route]);
  }

  switchMode() {
    const newRoute = this.mode === 'analyst' ? '/finance/chat' : '/analyst/chat';
    this.router.navigate([newRoute]);
  }

  startNewChat() {
    this.createNewSession();
  }

  selectSession(id: string) {
    const session = this.sessions.find(s => s.id === id);
    if (!session) return;
    this.currentSessionId = session.id;
    this.messages = [];
    this.loadMessages(session.id);
  }

  renameSession(session: ChatSession) {
    const nextTitle = window.prompt('Rename chat', session.title);
    if (!nextTitle || !nextTitle.trim()) return;

    this.chatService.renameSession(session.id, nextTitle.trim()).subscribe({
      next: (updated) => {
        this.sessions = this.sessions.map((s) =>
          s.id === updated.id ? this.mapSessionDto(updated) : s
        );
      }
    });
  }

  deleteSession(session: ChatSession) {
    if (!window.confirm('Delete this chat session? This cannot be undone.')) return;

    this.chatService.deleteSession(session.id).subscribe({
      next: () => {
        const remaining = this.sessions.filter(s => s.id !== session.id);
        this.sessions = remaining;
        if (this.currentSessionId === session.id) {
          if (remaining.length) {
            this.currentSessionId = remaining[0].id;
            this.loadMessages(this.currentSessionId);
          } else {
            this.currentSessionId = null;
            this.messages = [];
          }
        }
      }
    });
  }

  sendMessage(prompt?: string) {
    const text = prompt || this.userInput;
    if (!text.trim()) return;

    if (!this.currentSessionId) {
      this.createNewSession(() => this.sendMessage(text));
      return;
    }

    this.messages = [...this.messages, { role: 'user', content: text }];
    this.userInput = '';
    this.scrollToBottom();

    // Mettre un message de chargement temporaire
    const loadingMessageLevel = this.messages.length;
    this.messages = [...this.messages, { role: 'assistant', content: '...', isLoading: true }];
    this.scrollToBottom();

    // Appel reel au backend
    this.chatService.sendMessage(this.mode, text, this.currentSessionId).subscribe({
      next: (res) => {
        // Remplacer le message de chargement par la reponse reelle
        const updated = [...this.messages];
        updated[loadingMessageLevel] = {
          role: 'assistant',
          content: res.response,
          sources: res.sources
        };
        this.messages = updated;
        if (res.session_id && res.session_id !== this.currentSessionId) {
          this.currentSessionId = res.session_id;
        }
        this.refreshSessions();
        this.scrollToBottom();
      },
      error: (err) => {
        // En cas d'erreur
        const updated = [...this.messages];
        updated[loadingMessageLevel] = {
          role: 'assistant',
          content: "Sorry, I encountered an error while processing your request. Please try again later."
        };
        this.messages = updated;
        this.scrollToBottom();
        console.error("Chat API error:", err);
      }
    });
  }

  private loadSessions() {
    this.chatService.listSessions(this.mode).subscribe({
      next: (sessions) => {
        this.sessions = sessions.map(this.mapSessionDto);
        if (!this.sessions.length) {
          this.createNewSession();
          return;
        }
        this.currentSessionId = this.sessions[0].id;
        this.loadMessages(this.currentSessionId);
      },
      error: () => {
        this.sessions = [];
        this.messages = [];
      }
    });
  }

  private refreshSessions() {
    this.chatService.listSessions(this.mode).subscribe({
      next: (sessions) => {
        this.sessions = sessions.map(this.mapSessionDto);
      }
    });
  }

  private createNewSession(afterCreate?: () => void) {
    this.chatService.createSession(this.mode).subscribe({
      next: (session) => {
        const mapped = this.mapSessionDto(session);
        this.sessions = [mapped, ...this.sessions.filter(s => s.id !== mapped.id)];
        this.currentSessionId = mapped.id;
        this.messages = [];
        if (afterCreate) {
          afterCreate();
        }
      }
    });
  }

  private loadMessages(sessionId: string) {
    this.chatService.getMessages(sessionId).subscribe({
      next: (messages) => {
        this.messages = messages.map(this.mapMessageDto);
        this.scrollToBottom();
      },
      error: () => {
        this.messages = [];
      }
    });
  }

  private mapSessionDto = (session: ChatSessionDto): ChatSession => ({
    id: session.id,
    title: session.title,
    mode: session.mode,
    date: new Date(session.updated_at || session.created_at || new Date().toISOString())
  });

  private mapMessageDto = (message: ChatMessageDto): ChatMessage => ({
    role: message.role,
    content: message.content,
    sources: message.sources || []
  });

  private scrollToBottom(): void {
    if (!this.messageList) return;
    requestAnimationFrame(() => {
      const el = this.messageList?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    });
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  trackBySession(index: number, session: ChatSession): string {
    return session.id;
  }

  trackByMessage(index: number, msg: ChatMessage): string {
    return `${msg.role}-${index}`;
  }
}

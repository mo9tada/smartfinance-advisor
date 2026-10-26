import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { LawIngestionService } from '../../../core/services/law-ingestion.service';
import { IngestionLogLine } from '../../../core/models/trading.models';

@Component({
  selector: 'app-law-ingestion',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './law-ingestion.component.html'
})
export class LawIngestionComponent implements OnInit, OnDestroy {
  private lawIngestionService = inject(LawIngestionService);

  isIngesting = false;
  ingestionError: string | null = null;
  ingestionLogs: IngestionLogLine[] = [];
  ingestionExitCode: number | null = null;

  private ingestionPollTimer: ReturnType<typeof setInterval> | null = null;
  private lastLogId = 0;

  ngOnInit(): void {
    this.bootstrapState();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  startIngestion(): void {
    if (this.isIngesting) {
      return;
    }

    this.ingestionError = null;
    this.ingestionLogs = [];
    this.lastLogId = 0;
    this.ingestionExitCode = null;

    this.lawIngestionService
      .startIngestion()
      .pipe(finalize(() => {
        if (this.isIngesting) {
          this.startPolling();
        }
      }))
      .subscribe({
        next: () => {
          this.isIngesting = true;
        },
        error: (err) => {
          if (err?.status === 403) {
            this.ingestionError = 'Administrator access required.';
            return;
          }
          this.ingestionError = err?.error?.msg || 'Failed to start law ingestion.';
        }
      });
  }

  private bootstrapState(): void {
    this.lawIngestionService.getStatus().subscribe({
      next: (status) => {
        this.isIngesting = status.running;
        this.ingestionExitCode = status.exit_code;
        this.fetchLogs();

        if (status.running) {
          this.startPolling();
        }
      },
      error: (err) => {
        if (err?.status === 403) {
          this.ingestionError = 'Administrator access required.';
          return;
        }
        this.ingestionError = 'Could not load law ingestion status.';
      }
    });
  }

  private startPolling(): void {
    this.stopPolling();
    this.fetchLogs();

    this.ingestionPollTimer = setInterval(() => {
      this.fetchLogs();
    }, 1200);
  }

  private stopPolling(): void {
    if (this.ingestionPollTimer) {
      clearInterval(this.ingestionPollTimer);
      this.ingestionPollTimer = null;
    }
  }

  private fetchLogs(): void {
    this.lawIngestionService.getLogs(this.lastLogId).subscribe({
      next: (res) => {
        if (res.lines.length) {
          this.ingestionLogs = [...this.ingestionLogs, ...res.lines];
          this.lastLogId = res.next_from_id;
        }

        this.isIngesting = res.running;
        this.ingestionExitCode = res.exit_code;

        if (!res.running) {
          this.stopPolling();
        }
      },
      error: (err) => {
        this.stopPolling();
        this.isIngesting = false;

        if (err?.status === 403) {
          this.ingestionError = 'Administrator access required.';
          return;
        }

        this.ingestionError = err?.error?.msg || 'Failed to fetch law ingestion logs.';
      }
    });
  }
}

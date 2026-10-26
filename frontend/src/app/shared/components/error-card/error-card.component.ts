import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-error-card',
  standalone: true,
  template: `
    <div class="bg-rose-50 border border-rose-200 p-6 rounded-xl flex flex-col items-center gap-4 max-w-md mx-auto my-8">
      <div class="text-rose-600 text-4xl">⚠️</div>
      <div class="text-center">
        <h3 class="text-xl font-bold text-slate-900">{{ title }}</h3>
        <p class="text-slate-500 mt-2">{{ message }}</p>
      </div>
      <button 
        (click)="retry.emit()"
        class="bg-rose-600 hover:bg-rose-700 text-white px-6 py-2 rounded-lg font-semibold transition-colors shadow-sm">
        Retry
      </button>
    </div>
  `
})
export class ErrorCardComponent {
  @Input() title = 'Connection Error';
  @Input() message = 'Failed to fetch data from the server. Please check your connection and try again.';
  @Output() retry = new EventEmitter<void>();
}

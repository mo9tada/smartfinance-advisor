import { Component } from '@angular/core';

@Component({
    selector: 'app-loading-spinner',
    standalone: true,
    template: `
    <div class="flex items-center justify-center p-8">
      <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
    </div>
  `
})
export class LoadingSpinnerComponent { }

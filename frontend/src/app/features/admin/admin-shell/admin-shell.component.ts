import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-admin-shell',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="p-6">
      <div class="mb-8">
        <h1 class="text-2xl font-bold text-black mb-2">User Administration</h1>
        <p class="text-gray-400">Manage user registrations and account access.</p>
      </div>

      <nav class="flex space-x-4 mb-8 border-b border-gray-800 pb-0.5">
        <a routerLink="./pending" routerLinkActive="text-blue-500 border-b-2 border-blue-500"
          class="pb-3 text-sm font-medium text-gray-400 hover:text-red-800 transition-colors">
          Pending Requests
        </a>
        <a routerLink="./users" routerLinkActive="text-blue-500 border-b-2 border-blue-500"
          class="pb-3 text-sm font-medium text-gray-400 hover:text-red-800 transition-colors">
          Active Users
        </a>
        <a routerLink="./law-ingestion" routerLinkActive="text-blue-500 border-b-2 border-blue-500"
          class="pb-3 text-sm font-medium text-gray-400 hover:text-red-800 transition-colors">
          Law Ingestion
        </a>
      </nav>

      <router-outlet></router-outlet>
    </div>
  `
})
export class AdminShellComponent { }

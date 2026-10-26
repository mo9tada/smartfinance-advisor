import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService } from '../../../core/services/admin.service';

@Component({
  selector: 'app-pending-users',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pending-users.component.html'
})
export class PendingUsersComponent {
  private adminService = inject(AdminService);
  
  users = signal<any[]>([]);
  isLoading = signal(true);
  actionInProgress = signal<number | null>(null);

  constructor() {
    this.loadUsers();
  }

  loadUsers() {
    this.isLoading.set(true);
    this.adminService.getPendingUsers().subscribe({
      next: (data) => {
        this.users.set(data);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false)
    });
  }

  accept(id: number) {
    this.actionInProgress.set(id);
    this.adminService.acceptUser(id).subscribe({
      next: () => {
        this.actionInProgress.set(null);
        this.loadUsers();
      },
      error: () => this.actionInProgress.set(null)
    });
  }

  reject(id: number) {
    if (!confirm('Are you sure you want to reject this request?')) return;
    this.actionInProgress.set(id);
    this.adminService.rejectUser(id).subscribe({
      next: () => {
        this.actionInProgress.set(null);
        this.loadUsers();
      },
      error: () => this.actionInProgress.set(null)
    });
  }
}

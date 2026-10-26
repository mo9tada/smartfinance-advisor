import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AdminService } from '../../../core/services/admin.service';

@Component({
  selector: 'app-active-users',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './active-users.component.html'
})
export class ActiveUsersComponent {
  private adminService = inject(AdminService);
  private fb = inject(FormBuilder);
  
  users = signal<any[]>([]);
  isLoading = signal(true);
  editingUser = signal<any | null>(null);

  editForm = this.fb.group({
    first_name: ['', Validators.required],
    last_name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    phone: [''],
    role: ['', Validators.required]
  });

  constructor() {
    this.loadUsers();
  }

  loadUsers() {
    this.isLoading.set(true);
    this.adminService.getActiveUsers().subscribe({
      next: (data) => {
        this.users.set(data);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false)
    });
  }

  startEdit(user: any) {
    this.editingUser.set(user);
    const names = user.full_name.split(' ');
    this.editForm.patchValue({
      first_name: names[0],
      last_name: names.slice(1).join(' '),
      email: user.email,
      phone: user.phone,
      role: user.role
    });
  }

  cancelEdit() {
    this.editingUser.set(null);
  }

  saveEdit() {
    if (this.editForm.invalid || !this.editingUser()) return;
    const id = this.editingUser().id;
    this.adminService.updateUser(id, this.editForm.value).subscribe({
      next: () => {
        this.editingUser.set(null);
        this.loadUsers();
      }
    });
  }

  deleteUser(id: number) {
    if (!confirm('Are you sure you want to delete this user?')) return;
    this.adminService.deleteUser(id).subscribe({
      next: () => this.loadUsers()
    });
  }
}

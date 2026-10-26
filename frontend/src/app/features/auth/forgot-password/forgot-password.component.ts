import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './forgot-password.component.html'
})
export class ForgotPasswordComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  step = signal(1);
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  emailForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]]
  });

  codeForm = this.fb.group({
    code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
  });

  passwordForm = this.fb.group({
    password: ['', [Validators.required, Validators.minLength(6)]],
    confirmPassword: ['', [Validators.required]]
  }, { validators: this.passwordMatchValidator });

  passwordMatchValidator(g: any) {
    return g.get('password').value === g.get('confirmPassword').value
      ? null : { mismatch: true };
  }

  sendCode() {
    if (this.emailForm.invalid) return;
    this.isLoading.set(true);
    this.authService.forgotPassword(this.emailForm.value.email!).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.step.set(2);
        this.errorMessage.set(null);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.msg || 'Error sending code');
      }
    });
  }

  verifyCode() {
    if (this.codeForm.invalid) return;
    this.isLoading.set(true);
    this.authService.verifyCode(this.emailForm.value.email!, this.codeForm.value.code!).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.step.set(3);
        this.errorMessage.set(null);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.msg || 'Invalid code');
      }
    });
  }

  resetPassword() {
    if (this.passwordForm.invalid) return;
    this.isLoading.set(true);
    const data = {
      email: this.emailForm.value.email,
      code: this.codeForm.value.code,
      new_password: this.passwordForm.value.password
    };
    this.authService.resetPassword(data).subscribe({
      next: () => {
        this.router.navigate(['/login'], { queryParams: { reset: 'success' } });
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.msg || 'Error resetting password');
      }
    });
  }
}

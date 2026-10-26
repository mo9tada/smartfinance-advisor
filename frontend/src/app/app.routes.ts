import { Routes } from '@angular/router';
import { authGuard, adminGuard, guestGuard } from './core/guards/auth.guards';
import { DashboardLayoutComponent } from './layout/dashboard-layout/dashboard-layout.component';

export const routes: Routes = [
    { path: '', redirectTo: 'login', pathMatch: 'full' },
    {
        path: 'login',
        canActivate: [guestGuard],
        loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent)
    },
    {
        path: 'register',
        canActivate: [guestGuard],
        loadComponent: () => import('./features/auth/register/register.component').then(m => m.RegisterComponent)
    },
    {
        path: 'forgot-password',
        canActivate: [guestGuard],
        loadComponent: () => import('./features/auth/forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent)
    },
    {
        path: '',
        component: DashboardLayoutComponent,
        canActivate: [authGuard],
        children: [
            { path: 'dashboard', redirectTo: 'dashboard/overview', pathMatch: 'full' },
            {
                path: 'dashboard/overview',
                loadComponent: () => import('./features/overview/overview.component').then(m => m.OverviewComponent)
            },
            {
                path: 'dashboard/price-chart',
                loadComponent: () => import('./features/price-chart/price-chart.component').then(m => m.PriceChartComponent)
            },
            {
                path: 'dashboard/returns',
                loadComponent: () => import('./features/returns/returns.component').then(m => m.ReturnsComponent)
            },
            {
                path: 'dashboard/volatility',
                loadComponent: () => import('./features/volatility/volatility.component').then(m => m.VolatilityComponent)
            },
            {
                path: 'dashboard/drawdown',
                loadComponent: () => import('./features/drawdown/drawdown.component').then(m => m.DrawdownComponent)
            },
            {
                path: 'dashboard/predictions',
                loadComponent: () => import('./features/predictions/predictions.component').then(m => m.PredictionsComponent)
            },
            {
                path: 'admin',
                canActivate: [adminGuard],
                loadComponent: () => import('./features/admin/admin-shell/admin-shell.component').then(m => m.AdminShellComponent),
                children: [
                    { path: '', redirectTo: 'pending', pathMatch: 'full' },
                    {
                        path: 'pending',
                        loadComponent: () => import('./features/admin/pending-users/pending-users.component').then(m => m.PendingUsersComponent)
                    },
                    {
                        path: 'users',
                        loadComponent: () => import('./features/admin/active-users/active-users.component').then(m => m.ActiveUsersComponent)
                    },
                    {
                        path: 'law-ingestion',
                        loadComponent: () => import('./features/admin/law-ingestion/law-ingestion.component').then(m => m.LawIngestionComponent)
                    }
                ]
            },
            {
                path: 'finance',
                loadComponent: () => import('./features/finance/finance.component').then(m => m.FinanceComponent)
            },
            {
                path: 'analyst/chat',
                loadComponent: () => import('./features/chat/analyst-chat/analyst-chat.component').then(m => m.AnalystChatComponent)
            },
            {
                path: 'finance/chat',
                loadComponent: () => import('./features/chat/finance-chat/finance-chat.component').then(m => m.FinanceChatComponent)
            }
        ]
    },
    { path: '**', redirectTo: 'login' }
];

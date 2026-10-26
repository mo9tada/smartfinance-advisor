export interface User {
  id: number;
  full_name: string;
  email: string;
  role: 'viewer' | 'analyst' | 'administrator';
  matricule?: string;
}

export interface LoginCredentials {
  matricule: string;
  password?: string;
}

export interface RegisterData {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface KPIStats {
    avg_return: number;
    avg_volatility: number;
    max_drawdown: number;
    min_drawdown: number;
    max_range: number;
    total_rows: number;
}

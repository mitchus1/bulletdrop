export interface User {
  id: number;
  username: string;
  email: string;
  discord_id?: string;
  avatar_url?: string;
  bio?: string;
  custom_domain?: string;
  storage_used: number;
  storage_limit: number;
  upload_count: number;
  is_active: boolean;
  is_admin: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  loading: boolean;
  isAuthenticated: boolean;
}
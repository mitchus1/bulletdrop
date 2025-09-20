export interface User {
  id: number;
  username: string;
  email: string;
  discord_id?: string;
  google_id?: string;
  github_id?: string;
  avatar_url?: string;
  bio?: string;
  github_username?: string;
  discord_username?: string;
  telegram_username?: string;
  instagram_username?: string;
  background_image?: string;
  background_color?: string;
  favorite_song?: string;
  custom_domain?: string;
  preferred_domain_id?: number;
  storage_used: number;
  storage_limit: number;
  upload_count: number;
  is_active: boolean;
  is_admin: boolean;
  is_verified: boolean;
  is_premium?: boolean;
  premium_expires_at?: string;
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
  handleOAuthToken: (token: string) => Promise<boolean>;
  loading: boolean;
  isAuthenticated: boolean;
}
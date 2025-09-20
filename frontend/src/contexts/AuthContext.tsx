import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, LoginCredentials, RegisterCredentials, AuthContextType } from '../types/auth';
import { apiService } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!user && !!token;

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('token');

      if (storedToken) {
        apiService.setToken(storedToken);
        setToken(storedToken);

        try {
          const userData = await apiService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to get user data:', error);
          // Clear invalid token
          localStorage.removeItem('token');
          apiService.setToken(null);
          setToken(null);
        }
      }

      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      setLoading(true);
      const tokenData = await apiService.login(credentials);

      // Set token
      setToken(tokenData.access_token);
      apiService.setToken(tokenData.access_token);

      // Get user data
      const userData = await apiService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (credentials: RegisterCredentials) => {
    try {
      setLoading(true);
      const tokenData = await apiService.register(credentials);

      // Set token
      setToken(tokenData.access_token);
      apiService.setToken(tokenData.access_token);

      // Get user data
      const userData = await apiService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await apiService.logout();
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear auth state regardless of API call success
      setUser(null);
      setToken(null);
      apiService.setToken(null);
      localStorage.removeItem('token');
    }
  };

  const refreshUser = async () => {
    try {
      if (token && isAuthenticated) {
        const userData = await apiService.getCurrentUser();
        setUser(userData);
      }
    } catch (error) {
      console.error('Failed to refresh user data:', error);
      // If refresh fails, might be an auth issue
      if (error instanceof Error && error.message.includes('401')) {
        logout();
      }
    }
  };

  const handleOAuthToken = async (tokenFromUrl: string) => {
    try {
      setLoading(true);
      
      // Set token
      setToken(tokenFromUrl);
      apiService.setToken(tokenFromUrl);
      localStorage.setItem('token', tokenFromUrl);

      // Get user data
      const userData = await apiService.getCurrentUser();
      setUser(userData);
      
      return true;
    } catch (error) {
      console.error('Failed to handle OAuth token:', error);
      // Clear invalid token
      localStorage.removeItem('token');
      apiService.setToken(null);
      setToken(null);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    refreshUser,
    handleOAuthToken,
    loading,
    isAuthenticated,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
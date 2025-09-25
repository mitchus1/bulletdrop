/**
 * @fileoverview API Service Module
 *
 * This module provides a centralized service for making HTTP requests to the BulletDrop API.
 * It handles authentication, token management, and provides typed methods for all API endpoints.
 *
 * Features:
 * - Automatic JWT token management
 * - Type-safe API methods
 * - Error handling with proper HTTP status codes
 * - Upload progress tracking
 * - Local storage token persistence
 *
 * @author BulletDrop Team
 * @version 1.0.0
 */

import { User, LoginCredentials, RegisterCredentials, AuthToken } from '../types/auth';
import { Upload, UploadListResponse } from '../types/upload';

/** Base URL for the BulletDrop API */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Centralized API service class for interacting with the BulletDrop backend.
 *
 * This class provides methods for authentication, file uploads, user management,
 * and other API operations. It automatically handles JWT token management and
 * provides consistent error handling across all endpoints.
 *
 * @example
 * ```typescript
 * const api = new ApiService();
 * const user = await api.login({ username: 'john', password: 'secret' });
 * ```
 */
/**
 * Interface for rate limiting information from API responses
 */
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: number;
  userLimit?: number;
  userRemaining?: number;
  userReset?: number;
}

class ApiService {
  private baseURL: string;
  private token: string | null = null;
  public rateLimitInfo: RateLimitInfo | null = null;

  /**
   * Creates a new ApiService instance.
   *
   * @param baseURL - The base URL for the API (defaults to localhost:8000)
   */
  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('token');
  }

  /**
   * Sets the authentication token for API requests.
   *
   * @param token - JWT token to use for authenticated requests, or null to clear
   */
  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  /**
   * Makes an authenticated HTTP request to the API.
   *
   * @template T - The expected response type
   * @param endpoint - API endpoint path (e.g., '/auth/login')
   * @param options - Fetch options (method, body, headers, etc.)
   * @returns Promise that resolves to the typed response data
   * @throws Error if the request fails or returns an error status
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      // Extract rate limiting information from headers
      this.extractRateLimitInfo(response);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error occurred');
    }
  }

  /**
   * Extracts rate limiting information from response headers.
   *
   * @param response - The fetch Response object
   */
  private extractRateLimitInfo(response: Response): void {
    const headers = response.headers;

    // Extract IP-based rate limit headers
    const limit = headers.get('x-ratelimit-limit');
    const remaining = headers.get('x-ratelimit-remaining');
    const reset = headers.get('x-ratelimit-reset');

    // Extract user-based rate limit headers
    const userLimit = headers.get('x-user-ratelimit-limit');
    const userRemaining = headers.get('x-user-ratelimit-remaining');
    const userReset = headers.get('x-user-ratelimit-reset');

    if (limit && remaining && reset) {
      this.rateLimitInfo = {
        limit: parseInt(limit, 10),
        remaining: parseInt(remaining, 10),
        reset: parseInt(reset, 10),
        userLimit: userLimit ? parseInt(userLimit, 10) : undefined,
        userRemaining: userRemaining ? parseInt(userRemaining, 10) : undefined,
        userReset: userReset ? parseInt(userReset, 10) : undefined,
      };
    }
  }

  /**
   * Gets the current rate limit information from the last API call.
   *
   * @returns Current rate limit information or null if not available
   */
  getRateLimitInfo(): RateLimitInfo | null {
    return this.rateLimitInfo;
  }

  // ==================== Authentication Endpoints ====================

  /**
   * Authenticates a user with username and password.
   *
   * @param credentials - User login credentials
   * @returns Promise that resolves to an authentication token
   * @throws Error if login fails (invalid credentials, etc.)
   *
   * @example
   * ```typescript
   * const token = await api.login({ username: 'john', password: 'secret' });
   * console.log('Access token:', token.access_token);
   * ```
   */
  async login(credentials: LoginCredentials): Promise<AuthToken> {
    return this.request<AuthToken>('/login/json', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  /**
   * Registers a new user account.
   *
   * @param credentials - User registration credentials
   * @returns Promise that resolves to an authentication token
   * @throws Error if registration fails (username taken, invalid email, etc.)
   */
  async register(credentials: RegisterCredentials): Promise<AuthToken> {
    return this.request<AuthToken>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  /**
   * Gets the current authenticated user's information.
   *
   * @returns Promise that resolves to the current user data
   * @throws Error if not authenticated or token is invalid
   */
  async getCurrentUser(): Promise<User> {
    return this.request<User>('/me');
  }

  /**
   * Logs out the current user.
   *
   * @returns Promise that resolves to a logout confirmation message
   * @note This clears the token from the client but doesn't blacklist it on the server
   */
  async logout(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/logout', {
      method: 'POST',
    });
  }

  /**
   * Refreshes the current authentication token.
   *
   * @returns Promise that resolves to a new authentication token
   * @throws Error if the current token is invalid or expired
   */
  async refreshToken(): Promise<AuthToken> {
    return this.request<AuthToken>('/auth/refresh', {
      method: 'POST',
    });
  }

  // Upload endpoints
  async uploadFile(
    file: File,
    customName?: string,
    domainId?: number,
    isPublic: boolean = true,
    onProgress?: (progress: number) => void
  ): Promise<Upload> {
    const formData = new FormData();
    formData.append('file', file);
    if (customName) formData.append('custom_name', customName);
    if (domainId) formData.append('domain_id', domainId.toString());
    formData.append('is_public', isPublic.toString());

    const url = `${this.baseURL}/api/uploads/`;
    const headers: Record<string, string> = {};

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const progress = (e.loaded / e.total) * 100;
            onProgress(progress);
          }
        });
      }

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            reject(new Error('Invalid response format'));
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText);
            reject(new Error(errorData.detail || `HTTP error! status: ${xhr.status}`));
          } catch (e) {
            reject(new Error(`HTTP error! status: ${xhr.status}`));
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error occurred'));
      });

      xhr.open('POST', url);

      // Set headers
      Object.entries(headers).forEach(([key, value]) => {
        xhr.setRequestHeader(key, value);
      });

      xhr.send(formData);
    });
  }

  async getUserUploads(page: number = 1, perPage: number = 20): Promise<UploadListResponse> {
    return this.request<UploadListResponse>(`/api/uploads/?page=${page}&per_page=${perPage}`);
  }

  async getUpload(uploadId: number): Promise<Upload> {
    return this.request<Upload>(`/api/uploads/${uploadId}`);
  }

  async deleteUpload(uploadId: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/uploads/${uploadId}`, {
      method: 'DELETE',
    });
  }

  async updateUpload(
    uploadId: number,
    customName?: string,
    isPublic?: boolean
  ): Promise<Upload> {
    const body: any = {};
    if (customName !== undefined) body.custom_name = customName;
    if (isPublic !== undefined) body.is_public = isPublic;

    return this.request<Upload>(`/api/uploads/${uploadId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }

  // Domain endpoints
  async getAvailableDomains(): Promise<{ domains: any[] }> {
    return this.request<{ domains: any[] }>('/api/domains/');
  }

  async getMyDomains(): Promise<{ domains: any[] }> {
    return this.request<{ domains: any[] }>('/api/domains/my');
  }

  async claimDomain(domainId: number): Promise<any> {
    return this.request<any>(`/api/domains/claim/${domainId}`, {
      method: 'POST',
    });
  }

  // Admin endpoints
  async adminRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(`/admin${endpoint}`, options);
  }

  // API Key endpoints
  async generateApiKey(): Promise<{ api_key: string }> {
    return this.request<{ api_key: string }>(`/users/me/api-key`, {
      method: 'POST',
    });
  }

  async revokeApiKey(): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/users/me/api-key`, {
      method: 'DELETE',
    });
  }

  async getApiKeyStatus(): Promise<{ has_api_key: boolean }> {
    return this.request<{ has_api_key: boolean }>(`/users/me/api-key`);
  }
}

export const apiService = new ApiService();
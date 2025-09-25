/**
 * Analytics Service
 * 
 * Service for interacting with analytics and view tracking APIs.
 * Handles recording views and retrieving analytics data.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ViewCreate {
  user_agent?: string;
  referer?: string;
}

export interface ViewAnalytics {
  content_id: number;
  content_type: string;
  total_views: number;
  unique_viewers: number;
  views_today: number;
  views_this_week: number;
  views_this_month: number;
  recent_views: Array<{
    viewed_at: string;
    country?: string;
    referer?: string;
    viewer_user_id?: number;
  }>;
  top_countries: Array<{
    country: string;
    views: number;
  }>;
  hourly_distribution: any[];
}

export interface TrendingContent {
  trending_files: Array<{
    upload_id: number;
    filename: string;
    upload_url: string;
    view_count: number;
    unique_viewers: number;
    created_at: string;
  }>;
  trending_profiles: Array<{
    user_id: number;
    username: string;
    display_name?: string;
    avatar_url?: string;
    view_count: number;
    unique_viewers: number;
  }>;
  time_period: string;
}

export interface ViewStats {
  total_views: number;
  unique_viewers?: number;
  last_viewed?: string;
}

class AnalyticsService {
  private rateLimitCache = new Map<string, { until: number; retryAfter: number }>();
  private requestCache = new Map<string, { data: any; timestamp: number; promise?: Promise<any> }>();
  private readonly CACHE_TTL = 30000; // 30 seconds cache

  /**
   * Make an authenticated request to the analytics API with rate limit handling and caching
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount: number = 0
  ): Promise<T> {
    // Create a cache key based on endpoint and user token
    const token = localStorage.getItem('token');
    const cacheKey = `${endpoint}_${token}_${JSON.stringify(options.body || '')}`;

    // Check if we have a cached response that's still valid
    const cached = this.requestCache.get(cacheKey);
    if (cached && (Date.now() - cached.timestamp) < this.CACHE_TTL) {
      // If there's a pending promise, return it
      if (cached.promise) {
        return cached.promise;
      }
      // Return cached data
      return cached.data;
    }

    // Create the actual request promise
    const requestPromise = this.performRequest<T>(endpoint, options, retryCount, token, cacheKey);

    // Store the promise in cache to prevent duplicate requests
    this.requestCache.set(cacheKey, {
      data: null,
      timestamp: Date.now(),
      promise: requestPromise
    });

    try {
      const result = await requestPromise;

      // Cache the successful result
      this.requestCache.set(cacheKey, {
        data: result,
        timestamp: Date.now(),
        promise: undefined
      });

      // Clean up old cache entries
      setTimeout(() => {
        this.cleanupCache();
      }, this.CACHE_TTL);

      return result;
    } catch (error) {
      // Remove failed request from cache
      this.requestCache.delete(cacheKey);
      throw error;
    }
  }

  /**
   * Perform the actual HTTP request
   */
  private async performRequest<T>(
    endpoint: string,
    options: RequestInit,
    retryCount: number,
    token: string | null,
    cacheKey: string
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    // Check if this endpoint is currently rate limited
    const rateLimitKey = `${endpoint}_${token}`;
    const rateLimitInfo = this.rateLimitCache.get(rateLimitKey);

    if (rateLimitInfo && Date.now() < rateLimitInfo.until) {
      throw new Error(`Rate limited until ${new Date(rateLimitInfo.until).toLocaleTimeString()}`);
    }

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (response.status === 429) {
        // Extract retry-after header if available
        const retryAfter = response.headers.get('retry-after');
        const retryAfterSeconds = retryAfter ? parseInt(retryAfter, 10) : Math.pow(2, retryCount + 1);
        const until = Date.now() + (retryAfterSeconds * 1000);

        // Cache the rate limit info
        this.rateLimitCache.set(rateLimitKey, { until, retryAfter: retryAfterSeconds });

        // Clean up cache after rate limit expires
        setTimeout(() => {
          this.rateLimitCache.delete(rateLimitKey);
        }, retryAfterSeconds * 1000);

        // If this is our first retry, wait and try again
        if (retryCount < 2) {
          await new Promise(resolve => setTimeout(resolve, Math.min(retryAfterSeconds * 1000, 30000)));
          return this.performRequest<T>(endpoint, options, retryCount + 1, token, cacheKey);
        }

        throw new Error(`Rate limit exceeded. Retry after ${retryAfterSeconds}s`);
      }

      if (!response.ok) {
        throw new Error(`Analytics API error: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network error - check your connection');
      }
      throw error;
    }
  }

  /**
   * Clean up old cache entries
   */
  private cleanupCache(): void {
    const now = Date.now();
    for (const [key, entry] of this.requestCache.entries()) {
      if (now - entry.timestamp > this.CACHE_TTL) {
        this.requestCache.delete(key);
      }
    }
  }

  /**
   * Record a file view event
   */
  async recordFileView(uploadId: number, viewData: ViewCreate = {}): Promise<void> {
    try {
      // Auto-populate user agent and referer if available
      const data: ViewCreate = {
        user_agent: navigator.userAgent,
        referer: document.referrer || undefined,
        ...viewData
      };

      await this.request(`/api/analytics/views/file/${uploadId}`, {
        method: 'POST',
        body: JSON.stringify(data)
      });
    } catch (error) {
      // Silently fail for analytics - don't disrupt user experience
      console.debug('Failed to record file view:', error);
    }
  }

  /**
   * Record a profile view event
   */
  async recordProfileView(userId: number, viewData: ViewCreate = {}): Promise<void> {
    try {
      // Auto-populate user agent and referer if available
      const data: ViewCreate = {
        user_agent: navigator.userAgent,
        referer: document.referrer || undefined,
        ...viewData
      };

      await this.request(`/api/analytics/views/profile/${userId}`, {
        method: 'POST',
        body: JSON.stringify(data)
      });
    } catch (error) {
      // Silently fail for analytics - don't disrupt user experience
      console.debug('Failed to record profile view:', error);
    }
  }

  /**
   * Get comprehensive analytics for a file
   */
  async getFileAnalytics(uploadId: number): Promise<ViewAnalytics> {
    return this.request<ViewAnalytics>(`/api/analytics/views/file/${uploadId}`);
  }

  /**
   * Get comprehensive analytics for a profile
   */
  async getProfileAnalytics(userId: number): Promise<ViewAnalytics> {
    return this.request<ViewAnalytics>(`/api/analytics/views/profile/${userId}`);
  }

  /**
   * Get trending content
   */
  async getTrendingContent(timePeriod: '24h' | '7d' | '30d' = '24h'): Promise<TrendingContent> {
    return this.request<TrendingContent>(`/api/analytics/trending?time_period=${timePeriod}`);
  }

  /**
   * Get quick view statistics
   */
  async getQuickStats(contentType: 'file' | 'profile', contentId: number): Promise<ViewStats> {
    return this.request<ViewStats>(`/api/analytics/stats/${contentType}/${contentId}`);
  }

  /**
   * Get admin analytics overview
   */
  async getAdminOverview(): Promise<any> {
    return this.request<any>('/api/analytics/admin/overview');
  }

  /**
   * Utility function to automatically record view on component mount
   * This can be used in React components with useEffect
   */
  recordViewOnMount = (contentType: 'file' | 'profile', contentId: number) => {
    return () => {
      if (contentType === 'file') {
        this.recordFileView(contentId);
      } else if (contentType === 'profile') {
        this.recordProfileView(contentId);
      }
    };
  };

  /**
   * Format view count for display (e.g., 1.2K, 5.6M)
   */
  formatViewCount(count: number): string {
    if (count < 1000) {
      return count.toString();
    } else if (count < 1000000) {
      return (count / 1000).toFixed(1) + 'K';
    } else {
      return (count / 1000000).toFixed(1) + 'M';
    }
  }

  /**
   * Calculate view velocity (views per day) from time-based metrics
   */
  calculateViewVelocity(analytics: ViewAnalytics): {
    daily: number;
    weekly: number;
    monthly: number;
  } {
    return {
      daily: analytics.views_today,
      weekly: Math.round(analytics.views_this_week / 7),
      monthly: Math.round(analytics.views_this_month / 30)
    };
  }

  /**
   * Get engagement rate (unique viewers / total views)
   */
  getEngagementRate(analytics: ViewAnalytics): number {
    if (analytics.total_views === 0) return 0;
    return (analytics.unique_viewers / analytics.total_views) * 100;
  }
}

export const analyticsService = new AnalyticsService();
export default analyticsService;
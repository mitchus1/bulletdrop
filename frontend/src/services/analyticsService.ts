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
  /**
   * Make an authenticated request to the analytics API
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = localStorage.getItem('token');
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      ...options,
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`Analytics API error: ${response.status}`);
    }

    return response.json();
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
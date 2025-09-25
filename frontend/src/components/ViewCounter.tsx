/**
 * ViewCounter Component
 * 
 * A compact component for displaying view counts with optional analytics details.
 * Can be used for files, profiles, or any content with view tracking.
 */

import { useState, useEffect } from 'react';
import { EyeIcon, ChartBarIcon, UsersIcon } from '@heroicons/react/24/outline';
import { analyticsService, ViewStats } from '../services/analyticsService';

interface ViewCounterProps {
  contentType: 'file' | 'profile';
  contentId: number;
  showDetails?: boolean;
  compact?: boolean;
  className?: string;
}

export default function ViewCounter({ 
  contentType, 
  contentId, 
  showDetails = false, 
  compact = false,
  className = '' 
}: ViewCounterProps) {
  const [stats, setStats] = useState<ViewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await analyticsService.getQuickStats(contentType, contentId);
        setStats(data);
        setError(null);
      } catch (err) {
        setError('Failed to load view stats');
        console.error('Error fetching view stats:', err);
      } finally {
        setLoading(false);
      }
    };

    // Only fetch if we have a valid contentId
    if (contentId) {
      fetchStats();
    }
  }, [contentType, contentId]);

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 text-gray-500 ${className}`}>
        <EyeIcon className="w-4 h-4 animate-pulse" />
        <span className="text-sm">Loading...</span>
      </div>
    );
  }

  if (error || !stats) {
    return null; // Silently fail for analytics
  }

  const formatCount = (count: number) => {
    return analyticsService.formatViewCount(count);
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return null;
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffDays > 7) {
      return date.toLocaleDateString();
    } else if (diffDays > 0) {
      return `${diffDays}d ago`;
    } else if (diffHours > 0) {
      return `${diffHours}h ago`;
    } else if (diffMinutes > 0) {
      return `${diffMinutes}m ago`;
    } else {
      return 'Just now';
    }
  };

  if (compact) {
    return (
      <div className={`flex items-center space-x-1 text-gray-600 text-sm ${className}`}>
        <EyeIcon className="w-3 h-3" />
        <span>{formatCount(stats.total_views)}</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center space-x-4 text-gray-600 ${className}`}>
      {/* Total Views */}
      <div className="flex items-center space-x-2">
        <EyeIcon className="w-4 h-4" />
        <span className="text-sm font-medium">{formatCount(stats.total_views)} views</span>
      </div>

      {/* Unique Viewers (if available) */}
      {showDetails && stats.unique_viewers && (
        <div className="flex items-center space-x-2">
          <UsersIcon className="w-4 h-4" />
          <span className="text-sm">{formatCount(stats.unique_viewers)} unique</span>
        </div>
      )}

      {/* Last Viewed */}
      {showDetails && stats.last_viewed && (
        <div className="flex items-center space-x-2">
          <ChartBarIcon className="w-4 h-4" />
          <span className="text-sm">Last viewed {formatDate(stats.last_viewed)}</span>
        </div>
      )}
    </div>
  );
}
/**
 * TrendingContent Component
 * 
 * Displays trending files and profiles based on view activity.
 * Can be used on dashboards, home pages, or explore sections.
 */

import { useState, useEffect } from 'react';
import { EyeIcon, UsersIcon, ClockIcon } from '@heroicons/react/24/outline';
import { analyticsService, TrendingContent as TrendingData } from '../services/analyticsService';

interface TrendingContentProps {
  timePeriod?: '24h' | '7d' | '30d';
  maxItems?: number;
  showProfiles?: boolean;
  showFiles?: boolean;
  className?: string;
}

export default function TrendingContent({ 
  timePeriod = '24h',
  maxItems = 5,
  showProfiles = true,
  showFiles = true,
  className = '' 
}: TrendingContentProps) {
  const [trending, setTrending] = useState<TrendingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<'24h' | '7d' | '30d'>(timePeriod);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        setLoading(true);
        const data = await analyticsService.getTrendingContent(selectedPeriod);
        setTrending(data);
        setError(null);
      } catch (err) {
        setError('Failed to load trending content');
        console.error('Error fetching trending content:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTrending();
  }, [selectedPeriod]);

  const formatCount = (count: number) => {
    return analyticsService.formatViewCount(count);
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  const getPeriodLabel = (period: string) => {
    switch (period) {
      case '24h': return 'Last 24 Hours';
      case '7d': return 'Last 7 Days';
      case '30d': return 'Last 30 Days';
      default: return 'Last 24 Hours';
    }
  };

  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Trending Content</h3>
          <div className="animate-pulse bg-gray-200 h-6 w-24 rounded"></div>
        </div>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse bg-gray-100 h-16 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !trending) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        <p>Unable to load trending content</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with Time Period Selector */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Trending Content</h3>
        <select
          value={selectedPeriod}
          onChange={(e) => setSelectedPeriod(e.target.value as '24h' | '7d' | '30d')}
          className="text-sm border border-gray-300 rounded-lg px-3 py-1 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>

      {/* Trending Files */}
      {showFiles && trending.trending_files.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">🔥 Trending Files</h4>
          <div className="space-y-2">
            {trending.trending_files.slice(0, maxItems).map((file, index) => (
              <div key={file.upload_id} className="flex items-center p-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                {/* Rank */}
                <div className="flex-shrink-0 w-6 h-6 bg-gradient-to-r from-orange-400 to-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center mr-3">
                  {index + 1}
                </div>
                
                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.filename}
                    </p>
                    <span className="text-xs text-gray-500">
                      {formatTimeAgo(file.created_at)}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 mt-1">
                    <div className="flex items-center space-x-1 text-gray-600">
                      <EyeIcon className="w-3 h-3" />
                      <span className="text-xs">{formatCount(file.view_count)} views</span>
                    </div>
                    <div className="flex items-center space-x-1 text-gray-600">
                      <UsersIcon className="w-3 h-3" />
                      <span className="text-xs">{formatCount(file.unique_viewers)} unique</span>
                    </div>
                  </div>
                </div>

                {/* View Button */}
                <a
                  href={file.upload_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-shrink-0 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full hover:bg-blue-200 transition-colors"
                >
                  View
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trending Profiles */}
      {showProfiles && trending.trending_profiles.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">👤 Trending Profiles</h4>
          <div className="space-y-2">
            {trending.trending_profiles.slice(0, maxItems).map((profile, index) => (
              <div key={profile.user_id} className="flex items-center p-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                {/* Rank */}
                <div className="flex-shrink-0 w-6 h-6 bg-gradient-to-r from-purple-400 to-pink-500 text-white text-xs font-bold rounded-full flex items-center justify-center mr-3">
                  {index + 1}
                </div>
                
                {/* Avatar */}
                <div className="flex-shrink-0 mr-3">
                  {profile.avatar_url ? (
                    <img
                      src={profile.avatar_url}
                      alt={profile.username}
                      className="w-8 h-8 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                      <span className="text-xs font-medium text-gray-600">
                        {profile.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Profile Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {profile.display_name || profile.username}
                    </p>
                    {profile.display_name && (
                      <span className="text-xs text-gray-500">@{profile.username}</span>
                    )}
                  </div>
                  <div className="flex items-center space-x-4 mt-1">
                    <div className="flex items-center space-x-1 text-gray-600">
                      <EyeIcon className="w-3 h-3" />
                      <span className="text-xs">{formatCount(profile.view_count)} views</span>
                    </div>
                    <div className="flex items-center space-x-1 text-gray-600">
                      <UsersIcon className="w-3 h-3" />
                      <span className="text-xs">{formatCount(profile.unique_viewers)} unique</span>
                    </div>
                  </div>
                </div>

                {/* View Profile Button */}
                <button
                  onClick={() => {
                    // Navigate to profile - this would depend on your routing setup
                    window.location.href = `/profile/${profile.username}`;
                  }}
                  className="flex-shrink-0 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full hover:bg-purple-200 transition-colors"
                >
                  Profile
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {(!showFiles || trending.trending_files.length === 0) && 
       (!showProfiles || trending.trending_profiles.length === 0) && (
        <div className="text-center py-8 text-gray-500">
          <ClockIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p>No trending content for {getPeriodLabel(selectedPeriod).toLowerCase()}</p>
          <p className="text-sm mt-2">Check back later or try a different time period</p>
        </div>
      )}
    </div>
  );
}
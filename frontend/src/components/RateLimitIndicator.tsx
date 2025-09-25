import React from 'react';
import { useRateLimit } from '../hooks/useRateLimit';
import { useTheme } from '../contexts/ThemeContext';

interface RateLimitIndicatorProps {
  showDetails?: boolean;
  compact?: boolean;
}

const RateLimitIndicator: React.FC<RateLimitIndicatorProps> = ({
  showDetails = false,
  compact = false
}) => {
  const { rateLimitInfo, isNearLimit, formatTimeUntilReset, getRateLimitStatus } = useRateLimit();
  const { theme } = useTheme();

  if (!rateLimitInfo) {
    return null;
  }

  const status = getRateLimitStatus();

  const getStatusColor = () => {
    switch (status) {
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  const getStatusColorDark = () => {
    switch (status) {
      case 'critical':
        return 'text-red-400 bg-red-900/20 border-red-800';
      case 'warning':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-800';
      default:
        return 'text-green-400 bg-green-900/20 border-green-800';
    }
  };

  const ipUsagePercent = Math.round(
    ((rateLimitInfo.limit - rateLimitInfo.remaining) / rateLimitInfo.limit) * 100
  );

  const userUsagePercent = rateLimitInfo.userLimit && rateLimitInfo.userRemaining
    ? Math.round(
        ((rateLimitInfo.userLimit - rateLimitInfo.userRemaining) / rateLimitInfo.userLimit) * 100
      )
    : null;

  if (compact) {
    return (
      <div
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${
          theme === 'dark' ? getStatusColorDark() : getStatusColor()
        }`}
        title={`Rate Limit: ${rateLimitInfo.remaining}/${rateLimitInfo.limit} remaining`}
      >
        <div className={`w-2 h-2 rounded-full mr-1 ${
          status === 'critical' ? 'bg-red-500' :
          status === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
        }`}></div>
        {rateLimitInfo.remaining}/{rateLimitInfo.limit}
      </div>
    );
  }

  return (
    <div className={`p-3 rounded-lg border ${
      theme === 'dark' ? getStatusColorDark() : getStatusColor()
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-2 ${
            status === 'critical' ? 'bg-red-500' :
            status === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
          }`}></div>
          <span className="font-medium text-sm">Rate Limit Status</span>
        </div>
        {isNearLimit && (
          <span className="text-xs font-medium uppercase tracking-wide">
            Near Limit
          </span>
        )}
      </div>

      {showDetails && (
        <div className="mt-3 space-y-2 text-sm">
          {/* IP-based limits */}
          <div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600 dark:text-gray-400">IP Rate Limit</span>
              <span className="text-xs font-mono">
                {rateLimitInfo.remaining}/{rateLimitInfo.limit} ({ipUsagePercent}% used)
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
              <div
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  status === 'critical' ? 'bg-red-500' :
                  status === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${ipUsagePercent}%` }}
              ></div>
            </div>
          </div>

          {/* User-based limits (if authenticated) */}
          {rateLimitInfo.userLimit && rateLimitInfo.userRemaining !== undefined && (
            <div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600 dark:text-gray-400">User Rate Limit</span>
                <span className="text-xs font-mono">
                  {rateLimitInfo.userRemaining}/{rateLimitInfo.userLimit} ({userUsagePercent}% used)
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
                <div
                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${userUsagePercent}%` }}
                ></div>
              </div>
            </div>
          )}

          <div className="flex justify-between text-xs pt-1">
            <span className="text-gray-500 dark:text-gray-400">Resets in:</span>
            <span className="font-mono">{formatTimeUntilReset(rateLimitInfo.reset)}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default RateLimitIndicator;
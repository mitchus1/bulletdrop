import { useState, useEffect } from 'react';
import { apiService, RateLimitInfo } from '../services/api';

/**
 * Custom hook for tracking and displaying rate limit information
 */
export const useRateLimit = () => {
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null);
  const [isNearLimit, setIsNearLimit] = useState(false);

  useEffect(() => {
    // Check rate limit info periodically
    const checkRateLimit = () => {
      const info = apiService.getRateLimitInfo();
      if (info) {
        setRateLimitInfo(info);

        // Check if user is near rate limit (less than 10% remaining)
        const ipNearLimit = info.remaining / info.limit < 0.1;
        const userNearLimit = info.userRemaining && info.userLimit
          ? info.userRemaining / info.userLimit < 0.1
          : false;

        setIsNearLimit(ipNearLimit || userNearLimit);
      }
    };

    // Check immediately and then every 30 seconds
    checkRateLimit();
    const interval = setInterval(checkRateLimit, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatTimeUntilReset = (resetTimestamp: number): string => {
    const now = Math.floor(Date.now() / 1000);
    const secondsUntilReset = resetTimestamp - now;

    if (secondsUntilReset <= 0) {
      return 'Now';
    }

    const minutes = Math.floor(secondsUntilReset / 60);
    const seconds = secondsUntilReset % 60;

    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  const getRateLimitStatus = (): 'normal' | 'warning' | 'critical' => {
    if (!rateLimitInfo) return 'normal';

    const ipUsagePercent = (rateLimitInfo.limit - rateLimitInfo.remaining) / rateLimitInfo.limit;
    const userUsagePercent = rateLimitInfo.userLimit && rateLimitInfo.userRemaining
      ? (rateLimitInfo.userLimit - rateLimitInfo.userRemaining) / rateLimitInfo.userLimit
      : 0;

    const maxUsage = Math.max(ipUsagePercent, userUsagePercent);

    if (maxUsage > 0.9) return 'critical';
    if (maxUsage > 0.7) return 'warning';
    return 'normal';
  };

  return {
    rateLimitInfo,
    isNearLimit,
    formatTimeUntilReset,
    getRateLimitStatus,
  };
};
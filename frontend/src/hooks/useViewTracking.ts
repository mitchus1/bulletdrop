/**
 * useViewTracking Hook
 * 
 * Custom React hook for automatically tracking views when components mount.
 * Provides easy integration of view tracking into any component.
 */

import { useEffect } from 'react';
import { analyticsService } from '../services/analyticsService';

interface UseViewTrackingOptions {
  enabled?: boolean;
  delay?: number; // Delay in ms before recording view
}

/**
 * Hook to automatically track file views
 * 
 * @param uploadId - ID of the file to track
 * @param options - Configuration options
 */
export function useFileViewTracking(
  uploadId: number | null | undefined,
  options: UseViewTrackingOptions = {}
) {
  const { enabled = true, delay = 1000 } = options;

  useEffect(() => {
    if (!enabled || !uploadId) return;

    const timer = setTimeout(() => {
      analyticsService.recordFileView(uploadId);
    }, delay);

    return () => clearTimeout(timer);
  }, [uploadId, enabled, delay]);
}

/**
 * Hook to automatically track profile views
 * 
 * @param userId - ID of the user profile to track
 * @param options - Configuration options
 */
export function useProfileViewTracking(
  userId: number | null | undefined,
  options: UseViewTrackingOptions = {}
) {
  const { enabled = true, delay = 2000 } = options; // Longer delay for profile views

  useEffect(() => {
    if (!enabled || !userId) return;

    const timer = setTimeout(() => {
      analyticsService.recordProfileView(userId);
    }, delay);

    return () => clearTimeout(timer);
  }, [userId, enabled, delay]);
}

/**
 * Generic hook for view tracking
 * 
 * @param contentType - Type of content ('file' or 'profile')
 * @param contentId - ID of the content to track
 * @param options - Configuration options
 */
export function useViewTracking(
  contentType: 'file' | 'profile',
  contentId: number | null | undefined,
  options: UseViewTrackingOptions = {}
) {
  const { enabled = true, delay = 1000 } = options;

  useEffect(() => {
    if (!enabled || !contentId) return;

    const timer = setTimeout(() => {
      if (contentType === 'file') {
        analyticsService.recordFileView(contentId);
      } else if (contentType === 'profile') {
        analyticsService.recordProfileView(contentId);
      }
    }, delay);

    return () => clearTimeout(timer);
  }, [contentType, contentId, enabled, delay]);
}

/**
 * Hook for tracking scroll-based engagement
 * Records view only after user has scrolled a certain percentage
 * 
 * @param contentType - Type of content ('file' or 'profile')
 * @param contentId - ID of the content to track
 * @param scrollThreshold - Percentage of page user must scroll (0-100)
 */
export function useScrollBasedViewTracking(
  contentType: 'file' | 'profile',
  contentId: number | null | undefined,
  scrollThreshold: number = 25
) {
  useEffect(() => {
    if (!contentId) return;

    let hasTracked = false;

    const handleScroll = () => {
      if (hasTracked) return;

      const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
      
      if (scrollPercent >= scrollThreshold) {
        hasTracked = true;
        
        if (contentType === 'file') {
          analyticsService.recordFileView(contentId);
        } else if (contentType === 'profile') {
          analyticsService.recordProfileView(contentId);
        }
        
        window.removeEventListener('scroll', handleScroll);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [contentType, contentId, scrollThreshold]);
}

/**
 * Hook for tracking time-based engagement
 * Records view only after user has stayed on page for a certain duration
 * Pauses timer when page is hidden and resumes from where it left off
 * 
 * @param contentType - Type of content ('file' or 'profile')
 * @param contentId - ID of the content to track
 * @param duration - Time in milliseconds user must stay on page
 */
export function useTimeBasedViewTracking(
  contentType: 'file' | 'profile',
  contentId: number | null | undefined,
  duration: number = 5000 // 5 seconds
) {
  useEffect(() => {
    if (!contentId) return;

    let timeoutId: number;
    let startTime = Date.now();
    let accumulatedTime = 0; // Time already spent viewing
    let isVisible = !document.hidden;
    let hasTracked = false;

    const trackView = () => {
      if (hasTracked) return;
      hasTracked = true;
      
      if (contentType === 'file') {
        analyticsService.recordFileView(contentId);
      } else if (contentType === 'profile') {
        analyticsService.recordProfileView(contentId);
      }
    };

    const startTimer = (remainingTime: number) => {
      if (hasTracked || remainingTime <= 0) {
        if (remainingTime <= 0) trackView();
        return;
      }
      
      startTime = Date.now();
      timeoutId = window.setTimeout(() => {
        if (isVisible) {
          trackView();
        }
      }, remainingTime);
    };

    const handleVisibilityChange = () => {
      if (document.hidden && isVisible) {
        // User left the page - pause timer and accumulate time spent
        isVisible = false;
        clearTimeout(timeoutId);
        
        if (!hasTracked) {
          const timeSpent = Date.now() - startTime;
          accumulatedTime += timeSpent;
        }
      } else if (!document.hidden && !isVisible) {
        // User returned to the page - resume timer with remaining time
        isVisible = true;
        
        if (!hasTracked) {
          const remainingTime = duration - accumulatedTime;
          startTimer(remainingTime);
        }
      }
    };

    // Initialize - start the timer if page is visible
    if (isVisible) {
      startTimer(duration);
    }

    // Listen for visibility changes
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [contentType, contentId, duration]);
}

export default useViewTracking;
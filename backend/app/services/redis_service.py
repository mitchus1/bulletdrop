"""
Redis/Valkey Service Module

This module provides a centralized service for interacting with Valkey (Redis-compatible).
It handles caching, session management, view counting, and other Redis operations.

Classes:
    RedisService: Main service class for Redis operations
    CacheKeys: Constants for cache key patterns
"""

import redis
import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheKeys:
    """Constants for Redis cache key patterns"""
    USER_PROFILE = "user:profile:{user_id}"
    USER_COUNTS = "user:counts:{user_id}"
    FILE_METADATA = "file:meta:{filename}"
    VIEW_COUNT_FILE = "views:file:{upload_id}"
    VIEW_COUNT_PROFILE = "views:profile:{user_id}"
    TRENDING_FILES = "trending:files:{period}"
    TRENDING_PROFILES = "trending:profiles:{period}"
    ANALYTICS_CACHE = "analytics:{content_type}:{content_id}"
    JWT_USER_CACHE = "jwt:user:{username}"
    RATE_LIMIT = "rate:{endpoint}:{user_id}:{period}"


class RedisService:
    """
    Service class for Redis/Valkey operations.

    Provides methods for caching, view counting, analytics, and session management.
    Includes fallback mechanisms for when Redis is unavailable.
    """

    def __init__(self):
        """Initialize Redis connection with fallback handling."""
        self.redis_client = None
        self._connected = False
        self._connect()

    def _connect(self):
        """Establish connection to Redis/Valkey."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            self._connected = True
            logger.info("Successfully connected to Valkey")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis/Valkey: {e}")
            self._connected = False

    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        if not self._connected:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            self._connected = False
            return False

    def _safe_operation(self, operation, *args, **kwargs):
        """Execute Redis operation with fallback handling."""
        if not self.is_connected():
            logger.debug("Redis not available, skipping operation")
            return None

        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Redis operation failed: {e}")
            self._connected = False
            return None

    # ==================== User Profile Caching ====================

    def cache_user_profile(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        Cache user profile data.

        Args:
            user_id: User ID
            user_data: User profile data to cache

        Returns:
            True if cached successfully, False otherwise
        """
        key = CacheKeys.USER_PROFILE.format(user_id=user_id)
        return self._safe_operation(
            self.redis_client.setex,
            key,
            settings.CACHE_TTL_USER_PROFILE,
            json.dumps(user_data, default=str)
        ) is not None

    def get_cached_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached user profile data.

        Args:
            user_id: User ID

        Returns:
            Cached user data or None if not found
        """
        key = CacheKeys.USER_PROFILE.format(user_id=user_id)
        data = self._safe_operation(self.redis_client.get, key)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in cache for user {user_id}")
                self._safe_operation(self.redis_client.delete, key)

        return None

    def cache_user_counts(self, user_id: int, upload_count: int, storage_used: int) -> bool:
        """
        Cache user upload counts and storage usage.

        Args:
            user_id: User ID
            upload_count: Number of uploads
            storage_used: Storage used in bytes

        Returns:
            True if cached successfully
        """
        key = CacheKeys.USER_COUNTS.format(user_id=user_id)
        data = {
            "upload_count": upload_count,
            "storage_used": storage_used,
            "last_sync": datetime.utcnow().isoformat()
        }
        return self._safe_operation(
            self.redis_client.setex,
            key,
            settings.CACHE_TTL_USER_PROFILE,
            json.dumps(data)
        ) is not None

    def get_cached_user_counts(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user counts."""
        key = CacheKeys.USER_COUNTS.format(user_id=user_id)
        data = self._safe_operation(self.redis_client.get, key)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                self._safe_operation(self.redis_client.delete, key)

        return None

    # ==================== File Metadata Caching ====================

    def cache_file_metadata(self, filename: str, metadata: Dict[str, Any]) -> bool:
        """Cache file metadata for faster serving."""
        key = CacheKeys.FILE_METADATA.format(filename=filename)
        return self._safe_operation(
            self.redis_client.setex,
            key,
            settings.CACHE_TTL_FILE_METADATA,
            json.dumps(metadata, default=str)
        ) is not None

    def get_cached_file_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get cached file metadata."""
        key = CacheKeys.FILE_METADATA.format(filename=filename)
        data = self._safe_operation(self.redis_client.get, key)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                self._safe_operation(self.redis_client.delete, key)

        return None

    # ==================== View Counting ====================

    def increment_file_view(self, upload_id: int) -> Optional[int]:
        """
        Atomically increment file view count.

        Args:
            upload_id: Upload ID

        Returns:
            New view count or None if Redis unavailable
        """
        key = CacheKeys.VIEW_COUNT_FILE.format(upload_id=upload_id)
        pipeline = self._safe_operation(self.redis_client.pipeline)

        if pipeline:
            try:
                pipeline.hincrby(key, "total", 1)
                pipeline.hincrby(key, "today", 1)
                pipeline.expire(key, settings.CACHE_TTL_VIEW_COUNTS)
                results = pipeline.execute()
                return results[0] if results else None
            except Exception as e:
                logger.warning(f"Failed to increment view count: {e}")

        return None

    def get_file_view_count(self, upload_id: int) -> Optional[Dict[str, int]]:
        """Get cached file view counts."""
        key = CacheKeys.VIEW_COUNT_FILE.format(upload_id=upload_id)
        data = self._safe_operation(self.redis_client.hgetall, key)

        if data:
            try:
                return {k: int(v) for k, v in data.items()}
            except ValueError:
                self._safe_operation(self.redis_client.delete, key)

        return None

    def increment_profile_view(self, user_id: int) -> Optional[int]:
        """Atomically increment profile view count."""
        key = CacheKeys.VIEW_COUNT_PROFILE.format(user_id=user_id)
        return self._safe_operation(self.redis_client.incr, key)

    # ==================== Analytics Caching ====================

    def cache_analytics(self, content_type: str, content_id: int, analytics_data: Dict[str, Any]) -> bool:
        """Cache analytics data."""
        key = CacheKeys.ANALYTICS_CACHE.format(content_type=content_type, content_id=content_id)
        return self._safe_operation(
            self.redis_client.setex,
            key,
            settings.CACHE_TTL_ANALYTICS,
            json.dumps(analytics_data, default=str)
        ) is not None

    def get_cached_analytics(self, content_type: str, content_id: int) -> Optional[Dict[str, Any]]:
        """Get cached analytics data."""
        key = CacheKeys.ANALYTICS_CACHE.format(content_type=content_type, content_id=content_id)
        data = self._safe_operation(self.redis_client.get, key)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                self._safe_operation(self.redis_client.delete, key)

        return None

    # ==================== Trending Content ====================

    def add_to_trending(self, content_type: str, content_id: int, score: float = 1.0, period: str = "24h"):
        """Add content to trending sorted set."""
        key = CacheKeys.TRENDING_FILES.format(period=period) if content_type == "file" else CacheKeys.TRENDING_PROFILES.format(period=period)
        self._safe_operation(self.redis_client.zincrby, key, score, content_id)

        # Set expiration based on period
        ttl = 86400 if period == "24h" else 604800 if period == "7d" else 2592000  # 30d
        self._safe_operation(self.redis_client.expire, key, ttl)

    def get_trending(self, content_type: str, period: str = "24h", limit: int = 10) -> List[tuple]:
        """Get trending content from sorted set."""
        key = CacheKeys.TRENDING_FILES.format(period=period) if content_type == "file" else CacheKeys.TRENDING_PROFILES.format(period=period)
        return self._safe_operation(
            self.redis_client.zrevrange,
            key,
            0,
            limit - 1,
            withscores=True
        ) or []

    # ==================== JWT Caching ====================

    def cache_jwt_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Cache user data for JWT lookups."""
        key = CacheKeys.JWT_USER_CACHE.format(username=username)
        return self._safe_operation(
            self.redis_client.setex,
            key,
            1800,  # 30 minutes
            json.dumps(user_data, default=str)
        ) is not None

    def get_cached_jwt_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get cached user data for JWT lookups."""
        key = CacheKeys.JWT_USER_CACHE.format(username=username)
        data = self._safe_operation(self.redis_client.get, key)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                self._safe_operation(self.redis_client.delete, key)

        return None

    def invalidate_jwt_cache(self, username: str):
        """Invalidate JWT cache for user."""
        key = CacheKeys.JWT_USER_CACHE.format(username=username)
        self._safe_operation(self.redis_client.delete, key)

    # ==================== Rate Limiting ====================

    def check_rate_limit(self, endpoint: str, user_id: int, limit: int, period_seconds: int) -> bool:
        """
        Check if user has exceeded rate limit.

        Args:
            endpoint: API endpoint identifier
            user_id: User ID
            limit: Maximum requests allowed
            period_seconds: Time period in seconds

        Returns:
            True if within limit, False if exceeded
        """
        key = CacheKeys.RATE_LIMIT.format(endpoint=endpoint, user_id=user_id, period=period_seconds)
        current = self._safe_operation(self.redis_client.get, key)

        if current is None:
            # First request in period
            pipeline = self._safe_operation(self.redis_client.pipeline)
            if pipeline:
                try:
                    pipeline.setex(key, period_seconds, 1)
                    pipeline.execute()
                    return True
                except:
                    pass
            return True  # Allow if Redis fails

        try:
            current_count = int(current)
            if current_count >= limit:
                return False

            # Increment counter
            self._safe_operation(self.redis_client.incr, key)
            return True
        except:
            return True  # Allow if Redis fails

    # ==================== Utility Methods ====================

    def clear_user_cache(self, user_id: int):
        """Clear all cached data for a user."""
        keys = [
            CacheKeys.USER_PROFILE.format(user_id=user_id),
            CacheKeys.USER_COUNTS.format(user_id=user_id),
            CacheKeys.VIEW_COUNT_PROFILE.format(user_id=user_id)
        ]

        for key in keys:
            self._safe_operation(self.redis_client.delete, key)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis/cache statistics."""
        if not self.is_connected():
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "memory_used": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}


# Global instance
redis_service = RedisService()
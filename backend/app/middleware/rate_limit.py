"""
Rate Limiting Middleware

This module provides rate limiting functionality to protect against brute force attacks,
DDoS attempts, and API abuse. It uses Redis for distributed rate limiting and supports
different rate limits for different endpoint types.

Features:
- IP-based rate limiting
- User-based rate limiting (for authenticated endpoints)
- Different limits for authentication vs general API endpoints
- Sliding window algorithm for accurate rate limiting
- Automatic cleanup of expired rate limit data
- Configurable rate limits and time windows
"""

import time
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.redis_service import redis_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RateLimitConfig:
    """Rate limiting configuration for different endpoint types."""
    
    @classmethod
    def get_auth_limits(cls):
        return settings.RATE_LIMIT_AUTH_PER_MINUTE, settings.RATE_LIMIT_AUTH_PER_HOUR
    
    @classmethod
    def get_api_limits(cls):
        return settings.RATE_LIMIT_API_PER_MINUTE, settings.RATE_LIMIT_API_PER_HOUR
    
    @classmethod
    def get_upload_limits(cls):
        return settings.RATE_LIMIT_UPLOAD_PER_MINUTE, settings.RATE_LIMIT_UPLOAD_PER_HOUR
    
    @classmethod
    def get_admin_limits(cls):
        # Admin endpoints use same limits as general API
        return settings.RATE_LIMIT_API_PER_MINUTE, settings.RATE_LIMIT_API_PER_HOUR
    
    @classmethod
    def get_block_duration(cls):
        return settings.RATE_LIMIT_BLOCK_DURATION

class RateLimiter:
    """Redis-based rate limiter using sliding window algorithm."""
    
    def __init__(self):
        self.redis = redis_service
    
    async def is_rate_limited(self, key: str, limit: int, window: int) -> Tuple[bool, dict]:
        """
        Check if a key has exceeded the rate limit.
        
        Args:
            key: Unique identifier for the rate limit (e.g., "auth:ip:127.0.0.1")
            limit: Maximum number of requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_limited, rate_info)
        """
        try:
            now = time.time()
            pipeline = self.redis.client.pipeline()
            
            # Remove expired entries (sliding window)
            pipeline.zremrangebyscore(key, 0, now - window)
            
            # Count current requests in window
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(now): now})
            
            # Set expiry for the key (cleanup)
            pipeline.expire(key, window + 60)
            
            results = pipeline.execute()
            current_requests = results[1]
            
            # Calculate rate limit info
            reset_time = int(now + window)
            remaining = max(0, limit - current_requests - 1)  # -1 for current request
            
            rate_info = {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
                "current": current_requests + 1
            }
            
            return current_requests >= limit, rate_info
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # If Redis fails, allow the request (fail open)
            return False, {"limit": limit, "remaining": limit - 1, "reset": int(now + window)}
    
    async def block_ip(self, ip: str, duration: int = None):
        """Block an IP address for a specified duration."""
        try:
            if duration is None:
                duration = RateLimitConfig.get_block_duration()
            block_key = f"blocked:ip:{ip}"
            self.redis.client.setex(block_key, duration, "blocked")
        except Exception as e:
            logger.error(f"Error blocking IP {ip}: {e}")
    
    async def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP address is currently blocked."""
        try:
            block_key = f"blocked:ip:{ip}"
            return bool(self.redis.client.exists(block_key))
        except Exception as e:
            logger.error(f"Error checking if IP {ip} is blocked: {e}")
            return False
    
    async def is_ip_whitelisted(self, ip: str) -> bool:
        """Check if an IP address is whitelisted."""
        try:
            return bool(self.redis.client.sismember("rate_limit:whitelist", ip))
        except Exception as e:
            logger.error(f"Error checking if IP {ip} is whitelisted: {e}")
            return False
    
    async def add_to_whitelist(self, ip: str):
        """Add an IP to the whitelist."""
        try:
            self.redis.client.sadd("rate_limit:whitelist", ip)
            logger.info(f"Added IP {ip} to whitelist")
        except Exception as e:
            logger.error(f"Error adding IP {ip} to whitelist: {e}")
    
    async def remove_from_whitelist(self, ip: str):
        """Remove an IP from the whitelist."""
        try:
            self.redis.client.srem("rate_limit:whitelist", ip)
            logger.info(f"Removed IP {ip} from whitelist")
        except Exception as e:
            logger.error(f"Error removing IP {ip} from whitelist: {e}")
    
    async def get_whitelist(self) -> list:
        """Get all whitelisted IPs."""
        try:
            return list(self.redis.client.smembers("rate_limit:whitelist"))
        except Exception as e:
            logger.error(f"Error getting whitelist: {e}")
            return []

class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request headers."""
        # Check for forwarded IP headers (for proxy/load balancer setups)
        forwarded_ip = request.headers.get("X-Forwarded-For")
        if forwarded_ip:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_ip.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def get_rate_limit_key(self, request: Request, ip: str) -> str:
        """Generate rate limit key based on endpoint and IP."""
        path = request.url.path.lower()
        
        # Different prefixes for different endpoint types
        if any(auth_path in path for auth_path in ["/login", "/register", "/auth"]):
            return f"auth:ip:{ip}"
        elif "/upload" in path:
            return f"upload:ip:{ip}"
        elif "/admin" in path:
            return f"admin:ip:{ip}"
        else:
            return f"api:ip:{ip}"
    
    def get_rate_limits(self, request: Request) -> Tuple[int, int, int, int]:
        """Get rate limits for the current endpoint type."""
        path = request.url.path.lower()
        
        if any(auth_path in path for auth_path in ["/login", "/register", "/auth"]):
            minute_limit, hour_limit = RateLimitConfig.get_auth_limits()
            return minute_limit, 60, hour_limit, 3600
        elif "/upload" in path:
            minute_limit, hour_limit = RateLimitConfig.get_upload_limits()
            return minute_limit, 60, hour_limit, 3600
        elif "/admin" in path:
            minute_limit, hour_limit = RateLimitConfig.get_admin_limits()
            return minute_limit, 60, hour_limit, 3600
        else:
            minute_limit, hour_limit = RateLimitConfig.get_api_limits()
            return minute_limit, 60, hour_limit, 3600
    
    async def dispatch(self, request: Request, call_next):
        """Process rate limiting for incoming requests."""
        # Skip rate limiting if disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
            
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        ip = self.get_client_ip(request)
        
        # Check if IP is whitelisted (skip all rate limiting)
        if await self.rate_limiter.is_ip_whitelisted(ip):
            logger.debug(f"IP {ip} is whitelisted, skipping rate limiting")
            return await call_next(request)
        
        # Check if IP is blocked
        if await self.rate_limiter.is_ip_blocked(ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "IP address is temporarily blocked due to suspicious activity",
                    "retry_after": RateLimitConfig.get_block_duration()
                },
                headers={"Retry-After": str(RateLimitConfig.get_block_duration())}
            )
        
        # Get rate limits for this endpoint type
        minute_limit, minute_window, hour_limit, hour_window = self.get_rate_limits(request)
        
        # Check minute-based rate limit
        key_minute = f"{self.get_rate_limit_key(request, ip)}:1m"
        is_limited_minute, rate_info_minute = await self.rate_limiter.is_rate_limited(
            key_minute, minute_limit, minute_window
        )
        
        # Check hour-based rate limit
        key_hour = f"{self.get_rate_limit_key(request, ip)}:1h"
        is_limited_hour, rate_info_hour = await self.rate_limiter.is_rate_limited(
            key_hour, hour_limit, hour_window
        )
        
        # If either limit is exceeded
        if is_limited_minute or is_limited_hour:
            # For authentication endpoints, block IP after excessive attempts
            if "auth:ip:" in key_minute and is_limited_minute:
                await self.rate_limiter.block_ip(ip)
                logger.warning(f"IP {ip} blocked due to excessive authentication attempts")
            
            # Use the more restrictive limit for response
            active_rate_info = rate_info_minute if is_limited_minute else rate_info_hour
            limit_type = "minute" if is_limited_minute else "hour"
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": f"Rate limit exceeded: {active_rate_info['current']}/{active_rate_info['limit']} requests per {limit_type}",
                    "limit": active_rate_info["limit"],
                    "remaining": active_rate_info["remaining"],
                    "reset": active_rate_info["reset"],
                    "retry_after": active_rate_info["reset"] - int(time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(active_rate_info["limit"]),
                    "X-RateLimit-Remaining": str(active_rate_info["remaining"]),
                    "X-RateLimit-Reset": str(active_rate_info["reset"]),
                    "Retry-After": str(active_rate_info["reset"] - int(time.time()))
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(rate_info_minute["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info_minute["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info_minute["reset"])
        
        return response

# Utility functions for manual rate limiting in specific endpoints
async def check_rate_limit(request: Request, custom_limit: int = None, custom_window: int = None):
    """
    Manual rate limit check for specific endpoints.
    
    Args:
        request: FastAPI request object
        custom_limit: Override default rate limit
        custom_window: Override default time window
    
    Raises:
        HTTPException: If rate limit is exceeded
    """
    rate_limiter = RateLimiter()
    middleware = RateLimitMiddleware(None)
    
    ip = middleware.get_client_ip(request)
    key = middleware.get_rate_limit_key(request, ip)
    
    # Use custom limits or defaults
    if custom_limit and custom_window:
        limit, window = custom_limit, custom_window
    else:
        minute_limit, minute_window, _, _ = middleware.get_rate_limits(request)
        limit, window = minute_limit, minute_window
    
    is_limited, rate_info = await rate_limiter.is_rate_limited(key, limit, window)
    
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "limit": rate_info["limit"],
                "remaining": rate_info["remaining"],
                "reset": rate_info["reset"]
            },
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"]),
                "Retry-After": str(rate_info["reset"] - int(time.time()))
            }
        )

async def block_suspicious_ip(ip: str, duration: int = None):
    """Block an IP address for suspicious activity."""
    rate_limiter = RateLimiter()
    if duration is None:
        duration = RateLimitConfig.get_block_duration()
    await rate_limiter.block_ip(ip, duration)
    logger.warning(f"IP {ip} manually blocked for {duration} seconds")
"""
Rate Limiting Admin Endpoints

This module provides admin endpoints for managing rate limiting,
including viewing blocked IPs, manually blocking/unblocking IPs,
and monitoring rate limit statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.middleware.rate_limit import RateLimiter, block_suspicious_ip
from app.services.redis_service import redis_service

router = APIRouter()

def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.get("/rate-limits/blocked-ips")
async def get_blocked_ips(admin_user: User = Depends(require_admin)):
    """Get list of currently blocked IP addresses."""
    try:
        if not redis_service.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service unavailable"
            )
        
        # Scan for blocked IP keys
        blocked_ips = []
        for key in redis_service.client.scan_iter(match="blocked:ip:*"):
            ip = key.split(":")[-1]
            ttl = redis_service.client.ttl(key)
            blocked_ips.append({
                "ip": ip,
                "expires_in": ttl,
                "expires_at": datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
            })
        
        return {"blocked_ips": blocked_ips}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve blocked IPs: {str(e)}"
        )

@router.post("/rate-limits/block-ip")
async def block_ip(
    ip: str,
    duration: int = 300,
    reason: Optional[str] = None,
    admin_user: User = Depends(require_admin)
):
    """Manually block an IP address."""
    try:
        await block_suspicious_ip(ip, duration)
        
        # Log the manual block action
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Admin {admin_user.username} manually blocked IP {ip} for {duration}s. Reason: {reason or 'Not specified'}")
        
        return {
            "message": f"IP {ip} blocked successfully",
            "duration": duration,
            "blocked_by": admin_user.username,
            "reason": reason
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to block IP: {str(e)}"
        )

@router.delete("/rate-limits/unblock-ip/{ip}")
async def unblock_ip(ip: str, admin_user: User = Depends(require_admin)):
    """Manually unblock an IP address."""
    try:
        if not redis_service.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service unavailable"
            )
        
        block_key = f"blocked:ip:{ip}"
        was_blocked = redis_service.client.exists(block_key)
        
        # Remove from blocked list
        redis_service.client.delete(block_key)
        
        # Clear rate limit counters for this IP
        rate_keys = redis_service.client.keys(f"*:{ip}:*")
        if rate_keys:
            redis_service.client.delete(*rate_keys)
        
        # Log the unblock action
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Admin {admin_user.username} unblocked IP {ip}")
        
        return {
            "message": f"IP {ip} unblocked successfully",
            "was_blocked": bool(was_blocked),
            "unblocked_by": admin_user.username
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock IP: {str(e)}"
        )

@router.get("/rate-limits/whitelist")
async def get_whitelist(admin_user: User = Depends(require_admin)):
    """Get list of whitelisted IP addresses."""
    try:
        if not redis_service.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service unavailable"
            )
        
        whitelist = list(redis_service.client.smembers("rate_limit:whitelist"))
        return {"whitelisted_ips": whitelist}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve whitelist: {str(e)}"
        )

@router.post("/rate-limits/whitelist")
async def add_to_whitelist(
    ip: str,
    reason: Optional[str] = None,
    admin_user: User = Depends(require_admin)
):
    """Add an IP address to the whitelist."""
    try:
        if not redis_service.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service unavailable"
            )
        
        # Add to whitelist
        redis_service.client.sadd("rate_limit:whitelist", ip)
        
        # Also unblock the IP if it's currently blocked
        block_key = f"blocked:ip:{ip}"
        redis_service.client.delete(block_key)
        
        # Clear rate limit counters for this IP
        rate_keys = redis_service.client.keys(f"*:{ip}:*")
        if rate_keys:
            redis_service.client.delete(*rate_keys)
        
        # Log the whitelist action
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Admin {admin_user.username} added IP {ip} to whitelist. Reason: {reason or 'Not specified'}")
        
        return {
            "message": f"IP {ip} added to whitelist successfully",
            "added_by": admin_user.username,
            "reason": reason
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add IP to whitelist: {str(e)}"
        )

@router.delete("/rate-limits/whitelist/{ip}")
async def remove_from_whitelist(ip: str, admin_user: User = Depends(require_admin)):
    """Remove an IP address from the whitelist."""
    try:
        if not redis_service.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service unavailable"
            )
        
        was_whitelisted = redis_service.client.sismember("rate_limit:whitelist", ip)
        redis_service.client.srem("rate_limit:whitelist", ip)
        
        # Log the removal action
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Admin {admin_user.username} removed IP {ip} from whitelist")
        
        return {
            "message": f"IP {ip} removed from whitelist successfully",
            "was_whitelisted": bool(was_whitelisted),
            "removed_by": admin_user.username
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove IP from whitelist: {str(e)}"
        )
        
        if was_blocked:
            redis_service.client.delete(block_key)
            
            # Log the unblock action
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Admin {admin_user.username} manually unblocked IP {ip}")
            
            return {
                "message": f"IP {ip} unblocked successfully",
                "unblocked_by": admin_user.username
            }
        else:
            return {
                "message": f"IP {ip} was not blocked",
                "unblocked_by": admin_user.username
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock IP: {str(e)}"
        )

@router.get("/rate-limits/stats")
async def get_rate_limit_stats(admin_user: User = Depends(require_admin)):
    """Get rate limiting statistics."""
    try:
        if not redis_service.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service unavailable"
            )
        
        stats = {
            "blocked_ips_count": 0,
            "active_rate_limits": {
                "auth": 0,
                "api": 0,
                "upload": 0,
                "admin": 0
            },
            "top_rate_limited_ips": []
        }
        
        # Count blocked IPs
        blocked_count = 0
        for _ in redis_service.client.scan_iter(match="blocked:ip:*"):
            blocked_count += 1
        stats["blocked_ips_count"] = blocked_count
        
        # Count active rate limits by type
        rate_limit_counts = {"auth": 0, "api": 0, "upload": 0, "admin": 0}
        ip_request_counts = {}
        
        for key in redis_service.client.scan_iter(match="auth:ip:*"):
            rate_limit_counts["auth"] += 1
            ip = key.split(":")[2]
            count = redis_service.client.zcard(key)
            if ip not in ip_request_counts:
                ip_request_counts[ip] = 0
            ip_request_counts[ip] += count
        
        for key in redis_service.client.scan_iter(match="api:ip:*"):
            rate_limit_counts["api"] += 1
            ip = key.split(":")[2]
            count = redis_service.client.zcard(key)
            if ip not in ip_request_counts:
                ip_request_counts[ip] = 0
            ip_request_counts[ip] += count
        
        for key in redis_service.client.scan_iter(match="upload:ip:*"):
            rate_limit_counts["upload"] += 1
            ip = key.split(":")[2]
            count = redis_service.client.zcard(key)
            if ip not in ip_request_counts:
                ip_request_counts[ip] = 0
            ip_request_counts[ip] += count
        
        for key in redis_service.client.scan_iter(match="admin:ip:*"):
            rate_limit_counts["admin"] += 1
            ip = key.split(":")[2]
            count = redis_service.client.zcard(key)
            if ip not in ip_request_counts:
                ip_request_counts[ip] = 0
            ip_request_counts[ip] += count
        
        stats["active_rate_limits"] = rate_limit_counts
        
        # Get top rate-limited IPs
        top_ips = sorted(ip_request_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        stats["top_rate_limited_ips"] = [
            {"ip": ip, "request_count": count} for ip, count in top_ips
        ]
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rate limit stats: {str(e)}"
        )

@router.post("/rate-limits/clear-all")
async def clear_all_rate_limits(admin_user: User = Depends(require_admin)):
    """Clear all rate limiting data (use with caution)."""
    try:
        if not redis_service.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis service unavailable"
            )
        
        cleared_keys = 0
        
        # Clear all rate limit keys
        for pattern in ["auth:ip:*", "api:ip:*", "upload:ip:*", "admin:ip:*", "blocked:ip:*"]:
            for key in redis_service.client.scan_iter(match=pattern):
                redis_service.client.delete(key)
                cleared_keys += 1
        
        # Log the action
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Admin {admin_user.username} cleared all rate limiting data ({cleared_keys} keys)")
        
        return {
            "message": f"Cleared {cleared_keys} rate limiting keys",
            "cleared_by": admin_user.username
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear rate limits: {str(e)}"
        )
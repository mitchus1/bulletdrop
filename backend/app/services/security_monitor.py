"""
Security Monitoring Service

This module provides comprehensive security monitoring and alerting capabilities
for the BulletDrop application. It tracks security events, suspicious activities,
and potential threats.

Features:
- Failed login tracking
- Suspicious activity detection
- Rate limit violation monitoring
- IP blocking events
- Security event logging
- Real-time alerts and notifications
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from fastapi import Request

from app.services.redis_service import redis_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Types of security events to monitor."""
    FAILED_LOGIN = "failed_login"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IP_BLOCKED = "ip_blocked"
    IP_UNBLOCKED = "ip_unblocked"
    SUSPICIOUS_REQUEST = "suspicious_request"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    FILE_UPLOAD_VIOLATION = "file_upload_violation"
    ADMIN_ACTION = "admin_action"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKOUT = "account_lockout"


@dataclass
class SecurityEvent:
    """Represents a security event."""
    event_type: SecurityEventType
    timestamp: datetime
    ip_address: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    details: Dict[str, Any] = None
    severity: str = "medium"  # low, medium, high, critical
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    request_method: Optional[str] = None


class SecurityMonitor:
    """Main security monitoring service."""

    def __init__(self):
        self.redis = redis_service
        self.logger = logging.getLogger(f"{__name__}.SecurityMonitor")

    async def log_security_event(self, event: SecurityEvent):
        """
        Log a security event to both local logs and Redis for real-time monitoring.

        Args:
            event: SecurityEvent to log
        """
        # Create event record
        event_data = {
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "ip_address": event.ip_address,
            "user_id": event.user_id,
            "username": event.username,
            "details": event.details or {},
            "severity": event.severity,
            "user_agent": event.user_agent,
            "endpoint": event.endpoint,
            "request_method": event.request_method
        }

        # Log to application logger
        log_message = f"Security Event: {event.event_type.value} from {event.ip_address}"
        if event.username:
            log_message += f" (user: {event.username})"
        log_message += f" - {event.details}"

        if event.severity == "critical":
            self.logger.critical(log_message)
        elif event.severity == "high":
            self.logger.error(log_message)
        elif event.severity == "medium":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # Store in Redis for real-time monitoring
        if self.redis.is_connected():
            try:
                # Store individual event
                event_key = f"security_event:{event.timestamp.timestamp()}"
                self.redis.redis_client.setex(
                    event_key,
                    86400,  # Keep for 24 hours
                    json.dumps(event_data, default=str)
                )

                # Add to recent events list
                self.redis.redis_client.lpush("security_events:recent", json.dumps(event_data, default=str))
                self.redis.redis_client.ltrim("security_events:recent", 0, 999)  # Keep last 1000 events

                # Track by IP for pattern analysis
                ip_key = f"security_events:ip:{event.ip_address}"
                self.redis.redis_client.lpush(ip_key, json.dumps(event_data, default=str))
                self.redis.redis_client.expire(ip_key, 86400)  # Keep for 24 hours

                # Track by user if available
                if event.user_id:
                    user_key = f"security_events:user:{event.user_id}"
                    self.redis.redis_client.lpush(user_key, json.dumps(event_data, default=str))
                    self.redis.redis_client.expire(user_key, 86400)

                # Increment counters for dashboard
                counter_key = f"security_counters:{event.event_type.value}:{datetime.now().strftime('%Y-%m-%d-%H')}"
                self.redis.redis_client.incr(counter_key)
                self.redis.redis_client.expire(counter_key, 86400)

            except Exception as e:
                self.logger.error(f"Failed to store security event in Redis: {e}")

        # Check for suspicious patterns
        await self._analyze_suspicious_patterns(event)

    async def log_failed_login(self, ip_address: str, username: str, user_agent: str = None):
        """Log a failed login attempt."""
        event = SecurityEvent(
            event_type=SecurityEventType.FAILED_LOGIN,
            timestamp=datetime.now(),
            ip_address=ip_address,
            username=username,
            details={"attempted_username": username},
            severity="medium",
            user_agent=user_agent,
            endpoint="/auth/login",
            request_method="POST"
        )
        await self.log_security_event(event)

    async def log_rate_limit_exceeded(self, ip_address: str, endpoint: str, limit_type: str,
                                    user_id: int = None, username: str = None):
        """Log a rate limit violation."""
        severity = "high" if "auth" in endpoint else "medium"
        event = SecurityEvent(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_id=user_id,
            username=username,
            details={"endpoint": endpoint, "limit_type": limit_type},
            severity=severity,
            endpoint=endpoint
        )
        await self.log_security_event(event)

    async def log_ip_blocked(self, ip_address: str, reason: str = "excessive_requests"):
        """Log an IP blocking event."""
        event = SecurityEvent(
            event_type=SecurityEventType.IP_BLOCKED,
            timestamp=datetime.now(),
            ip_address=ip_address,
            details={"reason": reason},
            severity="high"
        )
        await self.log_security_event(event)

    async def log_suspicious_request(self, request: Request, reason: str, severity: str = "medium"):
        """Log a suspicious request."""
        ip_address = self._get_client_ip(request)
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_REQUEST,
            timestamp=datetime.now(),
            ip_address=ip_address,
            details={"reason": reason, "path": str(request.url.path)},
            severity=severity,
            user_agent=request.headers.get("user-agent"),
            endpoint=str(request.url.path),
            request_method=request.method
        )
        await self.log_security_event(event)

    async def log_admin_action(self, admin_user_id: int, admin_username: str, action: str,
                             target: str, ip_address: str):
        """Log an administrative action."""
        event = SecurityEvent(
            event_type=SecurityEventType.ADMIN_ACTION,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_id=admin_user_id,
            username=admin_username,
            details={"action": action, "target": target},
            severity="medium"
        )
        await self.log_security_event(event)

    async def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent security events for monitoring dashboard."""
        if not self.redis.is_connected():
            return []

        try:
            events = self.redis.redis_client.lrange("security_events:recent", 0, limit - 1)
            return [json.loads(event) for event in events]
        except Exception as e:
            self.logger.error(f"Failed to retrieve recent security events: {e}")
            return []

    async def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics for dashboard."""
        if not self.redis.is_connected():
            return {}

        try:
            current_hour = datetime.now().strftime('%Y-%m-%d-%H')
            stats = {}

            # Get current hour statistics
            for event_type in SecurityEventType:
                counter_key = f"security_counters:{event_type.value}:{current_hour}"
                count = self.redis.redis_client.get(counter_key)
                stats[event_type.value] = int(count) if count else 0

            # Get recent events count
            recent_count = self.redis.redis_client.llen("security_events:recent")
            stats["total_recent_events"] = recent_count

            return stats
        except Exception as e:
            self.logger.error(f"Failed to retrieve security stats: {e}")
            return {}

    async def get_ip_events(self, ip_address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get security events for a specific IP address."""
        if not self.redis.is_connected():
            return []

        try:
            ip_key = f"security_events:ip:{ip_address}"
            events = self.redis.redis_client.lrange(ip_key, 0, limit - 1)
            return [json.loads(event) for event in events]
        except Exception as e:
            self.logger.error(f"Failed to retrieve events for IP {ip_address}: {e}")
            return []

    async def _analyze_suspicious_patterns(self, event: SecurityEvent):
        """Analyze events for suspicious patterns and trigger alerts."""
        try:
            if event.event_type == SecurityEventType.FAILED_LOGIN:
                await self._check_brute_force_pattern(event.ip_address, event.username)
            elif event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED:
                await self._check_rate_limit_pattern(event.ip_address)
        except Exception as e:
            self.logger.error(f"Failed to analyze suspicious patterns: {e}")

    async def _check_brute_force_pattern(self, ip_address: str, username: str):
        """Check for brute force attack patterns."""
        if not self.redis.is_connected():
            return

        # Count failed logins from this IP in the last 10 minutes
        window_start = datetime.now() - timedelta(minutes=10)
        ip_events = await self.get_ip_events(ip_address, 100)

        recent_failed_logins = [
            event for event in ip_events
            if (event.get("event_type") == SecurityEventType.FAILED_LOGIN.value and
                datetime.fromisoformat(event.get("timestamp", "")) > window_start)
        ]

        if len(recent_failed_logins) >= 5:  # 5 failed logins in 10 minutes
            await self.log_security_event(SecurityEvent(
                event_type=SecurityEventType.BRUTE_FORCE_ATTEMPT,
                timestamp=datetime.now(),
                ip_address=ip_address,
                details={
                    "failed_attempts": len(recent_failed_logins),
                    "time_window": "10_minutes",
                    "target_username": username
                },
                severity="critical"
            ))

    async def _check_rate_limit_pattern(self, ip_address: str):
        """Check for excessive rate limit violations."""
        if not self.redis.is_connected():
            return

        # Count rate limit violations from this IP in the last hour
        window_start = datetime.now() - timedelta(hours=1)
        ip_events = await self.get_ip_events(ip_address, 200)

        recent_violations = [
            event for event in ip_events
            if (event.get("event_type") == SecurityEventType.RATE_LIMIT_EXCEEDED.value and
                datetime.fromisoformat(event.get("timestamp", "")) > window_start)
        ]

        if len(recent_violations) >= 10:  # 10 rate limit violations in 1 hour
            await self.log_security_event(SecurityEvent(
                event_type=SecurityEventType.SUSPICIOUS_REQUEST,
                timestamp=datetime.now(),
                ip_address=ip_address,
                details={
                    "rate_limit_violations": len(recent_violations),
                    "time_window": "1_hour",
                    "reason": "excessive_rate_limit_violations"
                },
                severity="high"
            ))

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def clear_events(self, event_type: Optional[str] = None, older_than_hours: Optional[int] = None) -> int:
        """
        Clear security events based on criteria.

        Args:
            event_type: Only clear events of this type
            older_than_hours: Only clear events older than this many hours

        Returns:
            Number of events cleared
        """
        if not self.redis.is_connected():
            return 0

        try:
            cleared_count = 0

            # Clear from recent events list
            if event_type or older_than_hours:
                events = self.redis.redis_client.lrange("security_events:recent", 0, -1)
                events_to_keep = []

                for event_json in events:
                    event = json.loads(event_json)
                    should_keep = True

                    # Check event type filter
                    if event_type and event.get("event_type") == event_type:
                        should_keep = False

                    # Check time filter
                    if older_than_hours and should_keep:
                        event_time = datetime.fromisoformat(event.get("timestamp", ""))
                        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
                        if event_time < cutoff_time:
                            should_keep = False

                    if should_keep:
                        events_to_keep.append(event_json)
                    else:
                        cleared_count += 1

                # Replace the list with filtered events
                if cleared_count > 0:
                    self.redis.redis_client.delete("security_events:recent")
                    if events_to_keep:
                        self.redis.redis_client.lpush("security_events:recent", *events_to_keep)

            else:
                # Clear all recent events
                cleared_count = self.redis.redis_client.llen("security_events:recent")
                self.redis.redis_client.delete("security_events:recent")

            # Clear counters if clearing all events
            if not event_type and not older_than_hours:
                # Get all counter keys and delete them
                counter_keys = self.redis.redis_client.keys("security_counters:*")
                if counter_keys:
                    self.redis.redis_client.delete(*counter_keys)

            return cleared_count

        except Exception as e:
            self.logger.error(f"Failed to clear security events: {e}")
            return 0

    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a specific security event by ID.

        Args:
            event_id: The event ID (timestamp) to delete

        Returns:
            True if event was found and deleted, False otherwise
        """
        if not self.redis.is_connected():
            return False

        try:
            # Try to delete the individual event key
            deleted = self.redis.redis_client.delete(f"security_event:{event_id}")

            # Also remove from recent events list if present
            events = self.redis.redis_client.lrange("security_events:recent", 0, -1)
            for i, event_json in enumerate(events):
                event = json.loads(event_json)
                if str(event.get("timestamp", "")).replace(":", "").replace("-", "").replace(".", "") == event_id:
                    self.redis.redis_client.lrem("security_events:recent", 1, event_json)
                    deleted = 1
                    break

            return deleted > 0

        except Exception as e:
            self.logger.error(f"Failed to delete security event {event_id}: {e}")
            return False


# Global security monitor instance
security_monitor = SecurityMonitor()
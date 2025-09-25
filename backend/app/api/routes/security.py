"""
Security Monitoring API Routes

This module provides API endpoints for security monitoring and administration.
Includes endpoints for viewing security events, statistics, and managing security alerts.

Endpoints:
    GET /admin/security/events - Get recent security events
    GET /admin/security/stats - Get security statistics
    GET /admin/security/ip/{ip_address} - Get events for specific IP
    POST /admin/security/alerts/test - Test security alert system
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from app.services.security_monitor import security_monitor, SecurityEventType

router = APIRouter(prefix="/admin/security", tags=["admin", "security"])


@router.get("/events", response_model=List[Dict[str, Any]])
async def get_security_events(
    limit: int = Query(100, le=500),
    event_type: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get recent security events for monitoring dashboard.

    Args:
        limit: Maximum number of events to return (max 500)
        event_type: Filter by specific event type
        current_admin: Current admin user
        db: Database session

    Returns:
        List of security events
    """
    try:
        events = await security_monitor.get_recent_events(limit)

        # Filter by event type if specified
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]

        return events

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security events: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_security_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get security statistics for the admin dashboard.

    Args:
        current_admin: Current admin user
        db: Database session

    Returns:
        Dictionary containing security statistics
    """
    try:
        stats = await security_monitor.get_security_stats()

        # Add timestamp for when stats were generated
        stats["generated_at"] = datetime.now().isoformat()
        stats["time_window"] = "current_hour"

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security statistics: {str(e)}"
        )


@router.get("/ip/{ip_address}", response_model=List[Dict[str, Any]])
async def get_ip_security_events(
    ip_address: str,
    limit: int = Query(50, le=200),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get security events for a specific IP address.

    Args:
        ip_address: IP address to query
        limit: Maximum number of events to return
        current_admin: Current admin user
        db: Database session

    Returns:
        List of security events for the specified IP
    """
    try:
        events = await security_monitor.get_ip_events(ip_address, limit)
        return events

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve events for IP {ip_address}: {str(e)}"
        )


@router.get("/event-types", response_model=List[str])
async def get_security_event_types(
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get list of available security event types for filtering.

    Args:
        current_admin: Current admin user

    Returns:
        List of security event type names
    """
    return [event_type.value for event_type in SecurityEventType]


@router.post("/alerts/test")
async def test_security_alert(
    event_type: str = "test_alert",
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Test the security monitoring system by generating a test event.

    Args:
        event_type: Type of test event to generate
        current_admin: Current admin user

    Returns:
        Confirmation of test event generation
    """
    try:
        from app.services.security_monitor import SecurityEvent

        test_event = SecurityEvent(
            event_type=SecurityEventType.ADMIN_ACTION,
            timestamp=datetime.now(),
            ip_address="127.0.0.1",
            user_id=current_admin.id,
            username=current_admin.username,
            details={
                "action": "test_security_alert",
                "test_event_type": event_type
            },
            severity="low"
        )

        await security_monitor.log_security_event(test_event)

        return {
            "message": "Test security event generated successfully",
            "event_type": event_type,
            "timestamp": test_event.timestamp.isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test security event: {str(e)}"
        )


@router.delete("/events/clear")
async def clear_security_events(
    event_type: Optional[str] = None,
    older_than_hours: Optional[int] = None,
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Clear security events based on criteria.

    Args:
        event_type: Only clear events of this type (optional)
        older_than_hours: Only clear events older than this many hours (optional)
        current_admin: Current admin user

    Returns:
        Confirmation of events cleared
    """
    try:
        cleared_count = await security_monitor.clear_events(
            event_type=event_type,
            older_than_hours=older_than_hours
        )

        # Log the admin action
        await security_monitor.log_admin_action(
            admin_user_id=current_admin.id,
            admin_username=current_admin.username,
            action="clear_security_events",
            target=f"event_type:{event_type or 'all'}, older_than:{older_than_hours or 'all'}",
            ip_address="127.0.0.1"  # Would need to extract from request
        )

        return {
            "message": f"Cleared {cleared_count} security events",
            "event_type": event_type,
            "older_than_hours": older_than_hours
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear security events: {str(e)}"
        )


@router.delete("/events/{event_id}")
async def delete_security_event(
    event_id: str,
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Delete a specific security event.

    Args:
        event_id: ID of the event to delete
        current_admin: Current admin user

    Returns:
        Confirmation of deletion
    """
    try:
        success = await security_monitor.delete_event(event_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Security event not found"
            )

        # Log the admin action
        await security_monitor.log_admin_action(
            admin_user_id=current_admin.id,
            admin_username=current_admin.username,
            action="delete_security_event",
            target=event_id,
            ip_address="127.0.0.1"
        )

        return {"message": "Security event deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete security event: {str(e)}"
        )


@router.get("/summary")
async def get_security_summary(
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get a summary of security status including recent threats and activity.

    Args:
        current_admin: Current admin user

    Returns:
        Security summary with key metrics and recent activity
    """
    try:
        # Get recent events
        recent_events = await security_monitor.get_recent_events(50)

        # Get current stats
        stats = await security_monitor.get_security_stats()

        # Calculate summary metrics
        total_events_today = sum(stats.values()) if isinstance(stats, dict) else 0

        # Count high severity events in last hour
        high_severity_events = [
            e for e in recent_events
            if e.get("severity") in ["high", "critical"] and
            datetime.fromisoformat(e.get("timestamp", "")) > datetime.now() - timedelta(hours=1)
        ]

        # Get most common event types
        event_type_counts = {}
        for event in recent_events[:100]:  # Last 100 events
            event_type = event.get("event_type", "unknown")
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        top_event_types = sorted(event_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "status": "healthy" if len(high_severity_events) < 5 else "warning",
            "total_events_today": total_events_today,
            "high_severity_events_last_hour": len(high_severity_events),
            "top_event_types": dict(top_event_types),
            "recent_critical_events": [
                e for e in recent_events[:20]
                if e.get("severity") == "critical"
            ],
            "monitoring_active": True,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate security summary: {str(e)}"
        )
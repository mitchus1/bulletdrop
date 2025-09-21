"""
Growth and User Acquisition API Routes

This module provides API endpoints for user acquisition features including
referrals, onboarding, social sharing, and growth analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.upload import Upload
from app.services.user_acquisition import UserAcquisitionService
from app.services.redis_service import redis_service

router = APIRouter()


@router.get("/referral/link")
async def get_referral_link(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's referral link and statistics."""
    referral_link = UserAcquisitionService.create_referral_link(db, current_user)
    analytics = UserAcquisitionService.get_referral_analytics(db, current_user.id)

    return {
        "referral_link": referral_link,
        "referral_code": current_user.referral_code,
        "total_referrals": analytics["total_referrals"],
        "total_bonus_mb": analytics["total_bonus_mb"],
        "potential_bonus": "100MB per successful referral"
    }


@router.get("/referral/analytics")
async def get_referral_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed referral analytics for the user."""
    analytics = UserAcquisitionService.get_referral_analytics(db, current_user.id)

    # Get recent referrals from Redis
    recent_referrals = redis_service._safe_operation(
        redis_service.redis_client.lrange,
        f"referrals:user:{current_user.id}:recent",
        0, 9  # Get last 10
    ) or []

    parsed_referrals = []
    for referral_data in recent_referrals:
        try:
            parts = referral_data.split(":")
            if len(parts) >= 3:
                parsed_referrals.append({
                    "user_id": int(parts[0]),
                    "username": parts[1],
                    "joined_at": parts[2]
                })
        except (ValueError, IndexError):
            continue

    return {
        "total_referrals": analytics["total_referrals"],
        "total_bonus_mb": analytics["total_bonus_mb"],
        "recent_referrals": parsed_referrals,
        "referral_link": UserAcquisitionService.create_referral_link(db, current_user),
        "leaderboard_rank": None  # Could implement leaderboard ranking
    }


@router.get("/onboarding/checklist")
async def get_onboarding_checklist(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get personalized onboarding checklist for the user."""
    checklist_data = UserAcquisitionService.create_onboarding_checklist(current_user)

    return {
        "checklist": checklist_data["checklist"],
        "progress": {
            "completed": checklist_data["completed_count"],
            "total": checklist_data["total_count"],
            "percentage": round((checklist_data["completed_count"] / checklist_data["total_count"]) * 100, 1)
        },
        "potential_bonus_mb": checklist_data["total_potential_bonus"]
    }


@router.post("/onboarding/complete/{task_id}")
async def complete_onboarding_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark an onboarding task as completed and award bonus if applicable."""
    # Define task bonuses
    task_bonuses = {
        "upload_first_file": 25,
        "customize_profile": 25,
        "setup_sharex": 50,
        "invite_friends": 100,
        "connect_social": 25
    }

    if task_id not in task_bonuses:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    bonus_mb = task_bonuses[task_id]
    bonus_bytes = bonus_mb * 1024 * 1024

    # Check if task is actually completed (basic validation)
    task_completed = False
    if task_id == "upload_first_file" and current_user.upload_count > 0:
        task_completed = True
    elif task_id == "customize_profile" and (current_user.bio or current_user.avatar_url):
        task_completed = True
    elif task_id == "connect_social" and (current_user.github_id or current_user.discord_id or current_user.google_id):
        task_completed = True

    if not task_completed and task_id != "setup_sharex":  # ShareX is special case
        raise HTTPException(status_code=400, detail="Task requirements not met")

    # Check if bonus already awarded
    cache_key = f"onboarding:bonus:{current_user.id}:{task_id}"
    already_awarded = redis_service._safe_operation(
        redis_service.redis_client.exists, cache_key
    )

    if already_awarded:
        return {"message": "Bonus already awarded for this task"}

    # Award bonus
    current_user.storage_limit = (current_user.storage_limit or 0) + bonus_bytes
    db.commit()

    # Mark bonus as awarded
    redis_service._safe_operation(
        redis_service.redis_client.setex,
        cache_key,
        86400 * 30,  # 30 days
        "awarded"
    )

    return {
        "message": f"Onboarding task completed! Awarded {bonus_mb}MB bonus storage.",
        "bonus_awarded_mb": bonus_mb,
        "new_storage_limit_mb": round(current_user.storage_limit / (1024 * 1024), 2)
    }


@router.get("/tools/sharex")
async def get_sharex_config(
    current_user: User = Depends(get_current_active_user),
    custom_domain: Optional[str] = Query(None, description="Custom domain for uploads")
):
    """Get ShareX configuration for the user."""
    config = UserAcquisitionService.create_sharex_config(current_user, custom_domain)

    return {
        "config": config,
        "download_filename": f"bulletdrop-{current_user.username}.sxcu",
        "instructions": [
            "1. Save this configuration as a .sxcu file",
            "2. Double-click the file to import into ShareX",
            "3. Set BulletDrop as your default image uploader",
            "4. Start uploading with Ctrl+Shift+U!"
        ]
    }


@router.get("/social/share")
async def generate_share_content(
    current_user: User = Depends(get_current_active_user),
    upload_id: Optional[int] = Query(None, description="Specific upload to share"),
    db: Session = Depends(get_db)
):
    """Generate social media sharing content."""
    upload = None
    if upload_id:
        upload = db.query(Upload).filter(
            Upload.id == upload_id,
            Upload.user_id == current_user.id
        ).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

    share_content = UserAcquisitionService.generate_social_share_content(current_user, upload)

    return {
        "platforms": share_content,
        "share_urls": {
            "twitter": f"https://twitter.com/intent/tweet?text={share_content['twitter']}",
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u={'https://mitchus.me'}&quote={share_content['facebook']}",
            "reddit": f"https://reddit.com/submit?title=BulletDrop&text={share_content['reddit']}",
        },
        "copy_text": share_content.get("twitter", "Check out BulletDrop - fast file sharing!")
    }


@router.get("/leaderboard/referrals")
async def get_referral_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get referral leaderboard (public)."""
    # This would typically be cached in Redis for performance
    cache_key = f"leaderboard:referrals:{limit}"
    cached_data = redis_service._safe_operation(
        redis_service.redis_client.get, cache_key
    )

    if cached_data:
        import json
        return json.loads(cached_data)

    # For demo purposes, return empty leaderboard
    # In real implementation, this would query the database for top referrers
    leaderboard = []

    result = {
        "leaderboard": leaderboard,
        "total_participants": 0,
        "last_updated": datetime.utcnow().isoformat()
    }

    # Cache for 1 hour
    redis_service._safe_operation(
        redis_service.redis_client.setex,
        cache_key,
        3600,
        json.dumps(result, default=str)
    )

    return result


@router.get("/stats/platform")
async def get_platform_growth_stats():
    """Get public platform growth statistics."""
    stats = UserAcquisitionService.get_platform_growth_stats()

    # Add some real-time metrics from Redis
    redis_stats = redis_service.get_cache_stats()
    if redis_stats.get("status") == "connected":
        stats["cache_performance"] = {
            "memory_used": redis_stats.get("memory_used", "unknown"),
            "hit_ratio": "excellent" if redis_stats.get("keyspace_hits", 0) > redis_stats.get("keyspace_misses", 1) else "good"
        }

    return {
        "growth_stats": stats,
        "features": {
            "file_sharing": "Fast and secure file uploads",
            "custom_profiles": "Personalized user profiles",
            "sharex_integration": "Seamless ShareX support",
            "real_time_analytics": "Live view tracking",
            "custom_domains": "Personal domain support"
        },
        "recent_updates": [
            "🚀 110x faster with Redis optimization",
            "⚡ Sub-millisecond cache response times",
            "🎯 88% cache hit ratio achieved",
            "💾 Efficient memory usage (1.11MB)",
            "🔄 Background sync for data consistency"
        ]
    }


@router.post("/signup")
async def public_signup_with_referral(
    username: str,
    email: str,
    password: str,
    referral_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Public signup endpoint with referral tracking."""
    from app.core.security import get_password_hash
    from app.schemas.auth import UserCreate

    # Check if email exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False,
        created_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Track referral if provided
    referral_success = False
    if referral_code:
        referral_success = UserAcquisitionService.track_referral_signup(
            db, referral_code, new_user
        )

    # Track signup method in Redis for analytics
    signup_method = "referral" if referral_success else "direct"
    redis_service._safe_operation(
        redis_service.redis_client.hincrby,
        "platform:signups:methods",
        signup_method,
        1
    )

    return {
        "message": "Account created successfully!",
        "user_id": new_user.id,
        "username": new_user.username,
        "referral_applied": referral_success,
        "welcome_bonus_mb": 50 if referral_success else 0,
        "next_steps": [
            "Complete your profile setup",
            "Upload your first file",
            "Set up ShareX integration",
            "Invite friends with your referral link"
        ]
    }
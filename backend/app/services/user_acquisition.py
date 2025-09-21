"""
User Acquisition Service

This module provides services for user acquisition, onboarding, referrals,
and growth features to help grow the BulletDrop user base.

Features:
    - Referral system with tracking and rewards
    - Onboarding flow optimization
    - User acquisition analytics
    - Growth marketing features
    - Social sharing tools
"""

import logging
import secrets
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.models.user import User
from app.models.upload import Upload
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class UserAcquisitionService:
    """Service for user acquisition and growth features."""

    @staticmethod
    def generate_referral_code(username: str) -> str:
        """Generate a unique referral code for a user."""
        # Create a memorable referral code based on username + random string
        random_suffix = secrets.token_urlsafe(4)[:4].upper()
        referral_code = f"{username.upper()[:4]}{random_suffix}"
        return referral_code

    @staticmethod
    def create_referral_link(db: Session, user: User) -> str:
        """Create a referral link for a user."""
        if not user.referral_code:
            # Generate referral code if user doesn't have one
            referral_code = UserAcquisitionService.generate_referral_code(user.username)

            # Ensure uniqueness
            existing = db.query(User).filter(User.referral_code == referral_code).first()
            while existing:
                referral_code = UserAcquisitionService.generate_referral_code(user.username)
                existing = db.query(User).filter(User.referral_code == referral_code).first()

            user.referral_code = referral_code
            db.commit()

        # Cache referral data for analytics
        referral_data = {
            "user_id": user.id,
            "username": user.username,
            "created_at": datetime.utcnow().isoformat(),
            "total_referrals": UserAcquisitionService.get_referral_count(db, user.id)
        }
        redis_service._safe_operation(
            redis_service.redis_client.setex,
            f"referral:code:{user.referral_code}",
            86400,  # 24 hours
            str(referral_data)
        )

        return f"https://mitchus.me/signup?ref={user.referral_code}"

    @staticmethod
    def track_referral_signup(db: Session, referral_code: str, new_user: User) -> bool:
        """Track a new user signup from a referral."""
        if not referral_code:
            return False

        # Find the referring user
        referring_user = db.query(User).filter(User.referral_code == referral_code).first()
        if not referring_user:
            logger.warning(f"Invalid referral code used: {referral_code}")
            return False

        # Update new user with referral info
        new_user.referred_by = referring_user.id

        # Track referral in Redis for real-time analytics
        redis_service._safe_operation(
            redis_service.redis_client.hincrby,
            f"referrals:user:{referring_user.id}",
            "total_referrals",
            1
        )

        # Track successful referral
        redis_service._safe_operation(
            redis_service.redis_client.lpush,
            f"referrals:user:{referring_user.id}:recent",
            f"{new_user.id}:{new_user.username}:{datetime.utcnow().isoformat()}"
        )

        # Limit recent referrals list to 50 items
        redis_service._safe_operation(
            redis_service.redis_client.ltrim,
            f"referrals:user:{referring_user.id}:recent",
            0, 49
        )

        # Award referral bonus (if applicable)
        UserAcquisitionService.award_referral_bonus(db, referring_user, new_user)

        db.commit()
        logger.info(f"Successful referral: {new_user.username} referred by {referring_user.username}")
        return True

    @staticmethod
    def award_referral_bonus(db: Session, referring_user: User, new_user: User):
        """Award bonus for successful referral."""
        # Award storage bonus to referring user (100MB bonus)
        storage_bonus = 100 * 1024 * 1024  # 100MB in bytes
        referring_user.storage_limit = (referring_user.storage_limit or 0) + storage_bonus

        # Give new user a welcome bonus too (50MB)
        welcome_bonus = 50 * 1024 * 1024  # 50MB in bytes
        new_user.storage_limit = (new_user.storage_limit or 0) + welcome_bonus

        # Track bonus in Redis for analytics
        redis_service._safe_operation(
            redis_service.redis_client.hincrby,
            f"referrals:user:{referring_user.id}",
            "total_bonus_mb",
            100
        )

        logger.info(f"Awarded referral bonus: {referring_user.username} (+100MB), {new_user.username} (+50MB)")

    @staticmethod
    def get_referral_count(db: Session, user_id: int) -> int:
        """Get total number of successful referrals for a user."""
        return db.query(func.count(User.id)).filter(User.referred_by == user_id).scalar() or 0

    @staticmethod
    def get_referral_analytics(db: Session, user_id: int) -> Dict[str, Any]:
        """Get comprehensive referral analytics for a user."""
        # Try Redis cache first
        cached_data = redis_service._safe_operation(
            redis_service.redis_client.hgetall,
            f"referrals:user:{user_id}"
        )

        if cached_data:
            return {
                "total_referrals": int(cached_data.get("total_referrals", 0)),
                "total_bonus_mb": int(cached_data.get("total_bonus_mb", 0)),
                "cached": True
            }

        # Fallback to database
        total_referrals = UserAcquisitionService.get_referral_count(db, user_id)

        # Calculate bonus awarded
        total_bonus = total_referrals * 100  # 100MB per referral

        analytics = {
            "total_referrals": total_referrals,
            "total_bonus_mb": total_bonus,
            "cached": False
        }

        # Cache for future requests
        redis_service._safe_operation(
            redis_service.redis_client.hmset,
            f"referrals:user:{user_id}",
            analytics
        )
        redis_service._safe_operation(
            redis_service.redis_client.expire,
            f"referrals:user:{user_id}",
            3600  # 1 hour
        )

        return analytics

    @staticmethod
    def create_sharex_config(user: User, custom_domain: Optional[str] = None) -> Dict[str, Any]:
        """Create a ShareX configuration for easy setup."""
        base_url = custom_domain or "https://mitchus.me"

        config = {
            "Version": "14.1.0",
            "Name": "BulletDrop",
            "DestinationType": "ImageUploader",
            "RequestMethod": "POST",
            "RequestURL": f"{base_url}/api/upload/sharex",
            "Headers": {
                "Authorization": f"Bearer {user.api_key}"
            },
            "Body": "MultipartFormData",
            "FileFormName": "file",
            "URL": "{json:url}",
            "DeletionURL": "{json:delete_url}",
            "ErrorMessage": "{json:error}"
        }

        # Track ShareX config downloads
        redis_service._safe_operation(
            redis_service.redis_client.hincrby,
            f"user:stats:{user.id}",
            "sharex_downloads",
            1
        )

        return config

    @staticmethod
    def get_platform_growth_stats() -> Dict[str, Any]:
        """Get overall platform growth statistics."""
        # Try Redis cache first
        cached_stats = redis_service._safe_operation(
            redis_service.redis_client.get,
            "platform:growth:stats"
        )

        if cached_stats:
            return json.loads(cached_stats)

        # This would typically come from database aggregations
        # For now, we'll return sample data that could be computed
        stats = {
            "total_users": 0,
            "users_this_week": 0,
            "users_this_month": 0,
            "total_uploads": 0,
            "uploads_this_week": 0,
            "referral_signups": 0,
            "oauth_signups": 0,
            "direct_signups": 0,
            "top_referrers": [],
            "growth_rate": 0.0
        }

        # Cache for 30 minutes
        redis_service._safe_operation(
            redis_service.redis_client.setex,
            "platform:growth:stats",
            1800,
            json.dumps(stats)
        )

        return stats

    @staticmethod
    def create_onboarding_checklist(user: User) -> Dict[str, Any]:
        """Create a personalized onboarding checklist for new users."""
        checklist = [
            {
                "id": "upload_first_file",
                "title": "Upload your first file",
                "description": "Try uploading an image or file to get started",
                "completed": (user.upload_count or 0) > 0,
                "bonus_mb": 25,
                "action_url": "/upload"
            },
            {
                "id": "customize_profile",
                "title": "Customize your profile",
                "description": "Add a bio, avatar, and social links",
                "completed": bool(user.bio or user.avatar_url),
                "bonus_mb": 25,
                "action_url": "/profile/edit"
            },
            {
                "id": "setup_sharex",
                "title": "Set up ShareX integration",
                "description": "Download and configure ShareX for quick uploads",
                "completed": False,  # Could track ShareX config downloads
                "bonus_mb": 50,
                "action_url": "/tools/sharex"
            },
            {
                "id": "invite_friends",
                "title": "Invite friends",
                "description": "Share your referral link and earn bonus storage",
                "completed": False,  # Would need DB session to check properly
                "bonus_mb": 100,
                "action_url": "/referrals"
            },
            {
                "id": "connect_social",
                "title": "Connect social accounts",
                "description": "Link your GitHub, Discord, or other social accounts",
                "completed": bool(user.github_id or user.discord_id or user.google_id),
                "bonus_mb": 25,
                "action_url": "/settings/social"
            }
        ]

        # Calculate stats
        completed_count = sum(1 for item in checklist if item["completed"])
        total_count = len(checklist)
        total_bonus = sum(item["bonus_mb"] for item in checklist if not item["completed"])

        return {
            "checklist": checklist,
            "total_potential_bonus": total_bonus,
            "completed_count": completed_count,
            "total_count": total_count
        }

    @staticmethod
    def generate_social_share_content(user: User, upload: Optional[Upload] = None) -> Dict[str, str]:
        """Generate social media sharing content."""
        if upload:
            # Sharing a specific upload
            content = {
                "twitter": f"Check out this file I shared on @BulletDrop! {upload.upload_url} #FileSharing #BulletDrop",
                "facebook": f"Sharing files made easy with BulletDrop! Check out: {upload.upload_url}",
                "discord": f"🚀 Shared via BulletDrop: {upload.upload_url}",
                "reddit": f"File shared via BulletDrop - {upload.upload_url}"
            }
        else:
            # Sharing profile or general platform
            profile_url = f"https://mitchus.me/profile/{user.username}"
            content = {
                "twitter": f"Check out my profile on @BulletDrop! Fast file sharing with custom profiles. {profile_url} #FileSharing",
                "facebook": f"Using BulletDrop for file sharing - it's fast, secure, and customizable! {profile_url}",
                "discord": f"🎯 My BulletDrop profile: {profile_url} - Fast file sharing platform!",
                "reddit": f"BulletDrop - Modern file sharing platform with custom profiles: {profile_url}"
            }

        return content
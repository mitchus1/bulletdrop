"""
Analytics Service

This module provides services for tracking and analyzing views on files and profiles.
Handles view recording, analytics aggregation, and trending content calculations.

Functions:
    record_file_view: Record a new file view
    record_profile_view: Record a new profile view
    get_file_analytics: Get analytics for a specific file
    get_profile_analytics: Get analytics for a specific profile
    get_trending_content: Get trending files and profiles
    get_view_summary: Get aggregated view statistics
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, text
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
from fastapi import Request

from app.models.views import FileView, ProfileView, ViewSummary
from app.models.upload import Upload
from app.models.user import User
from app.schemas.analytics import ViewCreate, ViewAnalytics, TrendingContent, ViewStatsResponse


class AnalyticsService:
    """Service class for handling view analytics and tracking."""
    
    @staticmethod
    def _hash_ip(ip: str) -> str:
        """
        Hash IP address for privacy protection.
        
        Args:
            ip: Raw IP address string
            
        Returns:
            Hashed IP address string
        """
        return hashlib.sha256(ip.encode()).hexdigest()[:32]
    
    @staticmethod
    def _extract_country_from_ip(ip: str) -> Optional[str]:
        """
        Extract country code from IP address.
        
        This is a placeholder implementation. In production, you would
        integrate with a GeoIP service like MaxMind or similar.
        
        Args:
            ip: IP address string
            
        Returns:
            Two-letter country code or None
        """
        # Placeholder implementation - in production, use a GeoIP service
        # Examples: maxmind, ipinfo.io, geojs.io
        return None
    
    @staticmethod
    def record_file_view(
        db: Session, 
        upload_id: int, 
        request: Request,
        view_data: ViewCreate,
        viewer_user_id: Optional[int] = None
    ) -> FileView:
        """
        Record a new file view event.
        
        Args:
            db: Database session
            upload_id: ID of the file being viewed
            request: FastAPI request object for IP extraction
            view_data: Additional view metadata
            viewer_user_id: ID of the user viewing (if logged in)
            
        Returns:
            Created FileView record
            
        Raises:
            ValueError: If upload doesn't exist
        """
        # Verify upload exists
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            raise ValueError(f"Upload with ID {upload_id} not found")
        
        # Extract IP address from request
        client_ip = request.client.host if request.client else "unknown"
        if request.headers.get("X-Forwarded-For"):
            client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        elif request.headers.get("X-Real-IP"):
            client_ip = request.headers["X-Real-IP"]
        
        # Hash IP for privacy
        hashed_ip = AnalyticsService._hash_ip(client_ip)
        
        # Create view record
        file_view = FileView(
            upload_id=upload_id,
            viewer_ip=hashed_ip,
            user_agent=view_data.user_agent,
            referer=view_data.referer,
            country=AnalyticsService._extract_country_from_ip(client_ip),
            viewed_at=datetime.utcnow()
        )
        
        db.add(file_view)
        
        # Update upload view count
        upload.view_count = (upload.view_count or 0) + 1
        
        db.commit()
        db.refresh(file_view)
        
        return file_view
    
    @staticmethod
    def record_profile_view(
        db: Session,
        profile_user_id: int,
        request: Request,
        view_data: ViewCreate,
        viewer_user_id: Optional[int] = None
    ) -> ProfileView:
        """
        Record a new profile view event.
        
        Args:
            db: Database session
            profile_user_id: ID of the user whose profile is being viewed
            request: FastAPI request object for IP extraction
            view_data: Additional view metadata
            viewer_user_id: ID of the user viewing (if logged in)
            
        Returns:
            Created ProfileView record
            
        Raises:
            ValueError: If profile user doesn't exist
        """
        # Verify profile user exists
        profile_user = db.query(User).filter(User.id == profile_user_id).first()
        if not profile_user:
            raise ValueError(f"User with ID {profile_user_id} not found")
        
        # Don't record self-views unless specifically requested
        if viewer_user_id == profile_user_id:
            # For now, we'll skip self-views. Could be configurable later.
            return None
        
        # Extract IP address from request
        client_ip = request.client.host if request.client else "unknown"
        if request.headers.get("X-Forwarded-For"):
            client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        elif request.headers.get("X-Real-IP"):
            client_ip = request.headers["X-Real-IP"]
        
        # Hash IP for privacy
        hashed_ip = AnalyticsService._hash_ip(client_ip)
        
        # Check for duplicate views within the last hour (simple deduplication)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        existing_view = db.query(ProfileView).filter(
            and_(
                ProfileView.profile_user_id == profile_user_id,
                ProfileView.viewer_ip == hashed_ip,
                ProfileView.viewed_at > one_hour_ago
            )
        ).first()
        
        if existing_view:
            return existing_view  # Don't create duplicate view
        
        # Create view record
        profile_view = ProfileView(
            profile_user_id=profile_user_id,
            viewer_ip=hashed_ip,
            viewer_user_id=viewer_user_id,
            user_agent=view_data.user_agent,
            referer=view_data.referer,
            country=AnalyticsService._extract_country_from_ip(client_ip),
            viewed_at=datetime.utcnow()
        )
        
        db.add(profile_view)
        db.commit()
        db.refresh(profile_view)
        
        return profile_view
    
    @staticmethod
    def get_file_analytics(db: Session, upload_id: int) -> ViewAnalytics:
        """
        Get comprehensive analytics for a specific file.
        
        Args:
            db: Database session
            upload_id: ID of the file to analyze
            
        Returns:
            ViewAnalytics object with comprehensive statistics
        """
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Total views
        total_views = db.query(func.count(FileView.id)).filter(
            FileView.upload_id == upload_id
        ).scalar() or 0
        
        # Unique viewers (by IP)
        unique_viewers = db.query(func.count(func.distinct(FileView.viewer_ip))).filter(
            FileView.upload_id == upload_id
        ).scalar() or 0
        
        # Views today
        views_today = db.query(func.count(FileView.id)).filter(
            and_(
                FileView.upload_id == upload_id,
                FileView.viewed_at >= today
            )
        ).scalar() or 0
        
        # Views this week
        views_this_week = db.query(func.count(FileView.id)).filter(
            and_(
                FileView.upload_id == upload_id,
                FileView.viewed_at >= week_ago
            )
        ).scalar() or 0
        
        # Views this month
        views_this_month = db.query(func.count(FileView.id)).filter(
            and_(
                FileView.upload_id == upload_id,
                FileView.viewed_at >= month_ago
            )
        ).scalar() or 0
        
        # Recent views (last 10)
        recent_views = db.query(FileView).filter(
            FileView.upload_id == upload_id
        ).order_by(desc(FileView.viewed_at)).limit(10).all()
        
        recent_views_data = [
            {
                "viewed_at": view.viewed_at.isoformat(),
                "country": view.country,
                "referer": view.referer
            }
            for view in recent_views
        ]
        
        # Top countries (if country data is available)
        top_countries_query = db.query(
            FileView.country,
            func.count(FileView.id).label('count')
        ).filter(
            and_(
                FileView.upload_id == upload_id,
                FileView.country.isnot(None)
            )
        ).group_by(FileView.country).order_by(desc('count')).limit(5)
        
        top_countries = [
            {"country": country, "views": count}
            for country, count in top_countries_query.all()
        ]
        
        return ViewAnalytics(
            content_id=upload_id,
            content_type="file",
            total_views=total_views,
            unique_viewers=unique_viewers,
            views_today=views_today,
            views_this_week=views_this_week,
            views_this_month=views_this_month,
            recent_views=recent_views_data,
            top_countries=top_countries,
            hourly_distribution=[]  # Could implement later
        )
    
    @staticmethod
    def get_profile_analytics(db: Session, user_id: int) -> ViewAnalytics:
        """
        Get comprehensive analytics for a specific user profile.
        
        Args:
            db: Database session
            user_id: ID of the user profile to analyze
            
        Returns:
            ViewAnalytics object with comprehensive statistics
        """
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Total views
        total_views = db.query(func.count(ProfileView.id)).filter(
            ProfileView.profile_user_id == user_id
        ).scalar() or 0
        
        # Unique viewers (by IP)
        unique_viewers = db.query(func.count(func.distinct(ProfileView.viewer_ip))).filter(
            ProfileView.profile_user_id == user_id
        ).scalar() or 0
        
        # Views today
        views_today = db.query(func.count(ProfileView.id)).filter(
            and_(
                ProfileView.profile_user_id == user_id,
                ProfileView.viewed_at >= today
            )
        ).scalar() or 0
        
        # Views this week
        views_this_week = db.query(func.count(ProfileView.id)).filter(
            and_(
                ProfileView.profile_user_id == user_id,
                ProfileView.viewed_at >= week_ago
            )
        ).scalar() or 0
        
        # Views this month
        views_this_month = db.query(func.count(ProfileView.id)).filter(
            and_(
                ProfileView.profile_user_id == user_id,
                ProfileView.viewed_at >= month_ago
            )
        ).scalar() or 0
        
        # Recent views (last 10)
        recent_views = db.query(ProfileView).filter(
            ProfileView.profile_user_id == user_id
        ).order_by(desc(ProfileView.viewed_at)).limit(10).all()
        
        recent_views_data = [
            {
                "viewed_at": view.viewed_at.isoformat(),
                "country": view.country,
                "referer": view.referer,
                "viewer_user_id": view.viewer_user_id
            }
            for view in recent_views
        ]
        
        return ViewAnalytics(
            content_id=user_id,
            content_type="profile",
            total_views=total_views,
            unique_viewers=unique_viewers,
            views_today=views_today,
            views_this_week=views_this_week,
            views_this_month=views_this_month,
            recent_views=recent_views_data,
            top_countries=[],  # Could implement later
            hourly_distribution=[]  # Could implement later
        )
    
    @staticmethod
    def get_trending_content(db: Session, time_period: str = "24h") -> TrendingContent:
        """
        Get trending files and profiles based on recent view activity.
        
        Args:
            db: Database session
            time_period: Time period for trending calculation ("24h", "7d", "30d")
            
        Returns:
            TrendingContent object with trending files and profiles
        """
        now = datetime.utcnow()
        
        # Calculate time cutoff
        if time_period == "24h":
            cutoff = now - timedelta(hours=24)
        elif time_period == "7d":
            cutoff = now - timedelta(days=7)
        elif time_period == "30d":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(hours=24)  # Default to 24h
        
        # Trending files
        trending_files_query = db.query(
            FileView.upload_id,
            func.count(FileView.id).label('view_count'),
            func.count(func.distinct(FileView.viewer_ip)).label('unique_viewers')
        ).join(Upload).filter(
            FileView.viewed_at >= cutoff
        ).group_by(FileView.upload_id).order_by(desc('view_count')).limit(10)
        
        trending_files = []
        for upload_id, view_count, unique_viewers in trending_files_query.all():
            upload = db.query(Upload).filter(Upload.id == upload_id).first()
            if upload:
                trending_files.append({
                    "upload_id": upload_id,
                    "filename": upload.original_filename,
                    "upload_url": upload.upload_url,
                    "view_count": view_count,
                    "unique_viewers": unique_viewers,
                    "created_at": upload.created_at.isoformat()
                })
        
        # Trending profiles
        trending_profiles_query = db.query(
            ProfileView.profile_user_id,
            func.count(ProfileView.id).label('view_count'),
            func.count(func.distinct(ProfileView.viewer_ip)).label('unique_viewers')
        ).join(User, ProfileView.profile_user_id == User.id).filter(
            ProfileView.viewed_at >= cutoff
        ).group_by(ProfileView.profile_user_id).order_by(desc('view_count')).limit(10)
        
        trending_profiles = []
        for user_id, view_count, unique_viewers in trending_profiles_query.all():
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                trending_profiles.append({
                    "user_id": user_id,
                    "username": user.username,
                    "display_name": user.display_name,
                    "avatar_url": user.avatar_url,
                    "view_count": view_count,
                    "unique_viewers": unique_viewers
                })
        
        return TrendingContent(
            trending_files=trending_files,
            trending_profiles=trending_profiles,
            time_period=time_period
        )
    
    @staticmethod
    def get_quick_stats(db: Session, content_type: str, content_id: int) -> ViewStatsResponse:
        """
        Get quick view statistics for a file or profile.
        
        Args:
            db: Database session
            content_type: Type of content ("file" or "profile")
            content_id: ID of the content
            
        Returns:
            ViewStatsResponse with quick statistics
        """
        if content_type == "file":
            total_views = db.query(func.count(FileView.id)).filter(
                FileView.upload_id == content_id
            ).scalar() or 0
            
            unique_viewers = db.query(func.count(func.distinct(FileView.viewer_ip))).filter(
                FileView.upload_id == content_id
            ).scalar() or 0
            
            last_viewed = db.query(func.max(FileView.viewed_at)).filter(
                FileView.upload_id == content_id
            ).scalar()
            
        elif content_type == "profile":
            total_views = db.query(func.count(ProfileView.id)).filter(
                ProfileView.profile_user_id == content_id
            ).scalar() or 0
            
            unique_viewers = db.query(func.count(func.distinct(ProfileView.viewer_ip))).filter(
                ProfileView.profile_user_id == content_id
            ).scalar() or 0
            
            last_viewed = db.query(func.max(ProfileView.viewed_at)).filter(
                ProfileView.profile_user_id == content_id
            ).scalar()
        else:
            raise ValueError(f"Invalid content type: {content_type}")
        
        return ViewStatsResponse(
            total_views=total_views,
            unique_viewers=unique_viewers,
            last_viewed=last_viewed
        )
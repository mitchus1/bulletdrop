"""
Analytics API Routes

This module defines FastAPI routes for view tracking and analytics.
Provides endpoints for recording views and retrieving analytics data.

Endpoints:
    POST /api/analytics/views/file/{upload_id} - Record a file view
    POST /api/analytics/views/profile/{user_id} - Record a profile view
    GET /api/analytics/views/file/{upload_id} - Get file analytics
    GET /api/analytics/views/profile/{user_id} - Get profile analytics
    GET /api/analytics/trending - Get trending content
    GET /api/analytics/stats/{content_type}/{content_id} - Get quick stats
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_optional, get_current_admin
from app.models.user import User
from app.schemas.analytics import (
    ViewCreate, 
    ViewAnalytics, 
    TrendingContent, 
    ViewStatsResponse,
    FileViewResponse,
    ProfileViewResponse
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.post("/views/file/{upload_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
async def record_file_view(
    upload_id: int,
    request: Request,
    view_data: ViewCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Record a new file view event.
    
    This endpoint is called when a user views a file/image. It tracks
    the view for analytics purposes while maintaining user privacy.
    
    Args:
        upload_id: ID of the file being viewed
        request: FastAPI request object (for IP extraction)
        view_data: Additional view metadata (user agent, referer)
        current_user: Currently logged-in user (optional)
        
    Returns:
        Success message with view ID
        
    Raises:
        404: If the file doesn't exist
        500: If view recording fails
    """
    try:
        viewer_user_id = current_user.id if current_user else None
        
        file_view = AnalyticsService.record_file_view(
            db=db,
            upload_id=upload_id,
            request=request,
            view_data=view_data,
            viewer_user_id=viewer_user_id
        )
        
        return {
            "message": "File view recorded successfully",
            "view_id": file_view.id,
            "upload_id": upload_id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record file view: {str(e)}"
        )


@router.post("/views/profile/{user_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
async def record_profile_view(
    user_id: int,
    request: Request,
    view_data: ViewCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Record a new profile view event.
    
    This endpoint is called when a user visits another user's profile.
    Self-views are automatically filtered out.
    
    Args:
        user_id: ID of the user whose profile is being viewed
        request: FastAPI request object (for IP extraction)
        view_data: Additional view metadata (user agent, referer)
        current_user: Currently logged-in user (optional)
        
    Returns:
        Success message with view ID
        
    Raises:
        404: If the profile user doesn't exist
        500: If view recording fails
    """
    try:
        viewer_user_id = current_user.id if current_user else None
        
        profile_view = AnalyticsService.record_profile_view(
            db=db,
            profile_user_id=user_id,
            request=request,
            view_data=view_data,
            viewer_user_id=viewer_user_id
        )
        
        if profile_view is None:
            # Self-view or duplicate view - still return success
            return {
                "message": "Profile view skipped (self-view or duplicate)",
                "profile_user_id": user_id
            }
        
        return {
            "message": "Profile view recorded successfully",
            "view_id": profile_view.id,
            "profile_user_id": user_id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record profile view: {str(e)}"
        )


@router.get("/views/file/{upload_id}", response_model=ViewAnalytics)
async def get_file_analytics(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get comprehensive analytics for a specific file.
    
    Returns detailed view statistics including total views, unique viewers,
    time-based metrics, and geographic distribution.
    
    Args:
        upload_id: ID of the file to analyze
        current_user: Currently logged-in user (for access control)
        
    Returns:
        ViewAnalytics object with comprehensive statistics
        
    Raises:
        404: If the file doesn't exist
        403: If user doesn't have access to view analytics
    """
    try:
        # Check if the upload exists
        from app.models.upload import Upload
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        # Implement access control - only file owner or admin can view detailed analytics
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view file analytics"
            )

        # Check if user owns the file or is an admin
        if upload.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view analytics for this file"
            )

        analytics = AnalyticsService.get_file_analytics(db=db, upload_id=upload_id)
        return analytics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve file analytics: {str(e)}"
        )


@router.get("/views/profile/{user_id}", response_model=ViewAnalytics)
async def get_profile_analytics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get comprehensive analytics for a specific user profile.
    
    Returns detailed view statistics including total views, unique viewers,
    and recent activity.
    
    Args:
        user_id: ID of the user profile to analyze
        current_user: Currently logged-in user (for access control)
        
    Returns:
        ViewAnalytics object with comprehensive statistics
        
    Raises:
        404: If the profile user doesn't exist
        403: If user doesn't have access to view analytics
    """
    try:
        # Check if the user exists
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Implement access control - only profile owner or admin can view detailed analytics
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view profile analytics"
            )

        # Check if user owns the profile or is an admin
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view analytics for this profile"
            )

        analytics = AnalyticsService.get_profile_analytics(db=db, user_id=user_id)
        return analytics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile analytics: {str(e)}"
        )


@router.get("/trending", response_model=TrendingContent)
async def get_trending_content(
    time_period: str = "24h",
    db: Session = Depends(get_db)
):
    """
    Get trending files and profiles based on recent view activity.
    
    Returns the most popular content based on view counts and unique viewers
    for the specified time period.
    
    Args:
        time_period: Time period for trending calculation ("24h", "7d", "30d")
        
    Returns:
        TrendingContent object with trending files and profiles
        
    Raises:
        400: If time_period is invalid
        500: If trending calculation fails
    """
    try:
        if time_period not in ["24h", "7d", "30d"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time period. Must be '24h', '7d', or '30d'"
            )
        
        trending = AnalyticsService.get_trending_content(db=db, time_period=time_period)
        return trending
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve trending content: {str(e)}"
        )


@router.get("/stats/{content_type}/{content_id}", response_model=ViewStatsResponse)
async def get_quick_stats(
    content_type: str,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get quick view statistics for a file or profile.
    
    Provides a lightweight endpoint for getting basic view counts
    without the full analytics data.
    
    Args:
        content_type: Type of content ("file" or "profile")
        content_id: ID of the content
        current_user: Currently logged-in user (for access control)
        
    Returns:
        ViewStatsResponse with quick statistics
        
    Raises:
        400: If content_type is invalid
        404: If content doesn't exist
        500: If stats retrieval fails
    """
    try:
        if content_type not in ["file", "profile"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content type. Must be 'file' or 'profile'"
            )
        
        stats = AnalyticsService.get_quick_stats(
            db=db, 
            content_type=content_type, 
            content_id=content_id
        )
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quick stats: {str(e)}"
        )


# Admin-only endpoints for comprehensive analytics
@router.get("/admin/overview", response_model=dict)
async def get_admin_analytics_overview(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get comprehensive analytics overview for administrators.
    
    Provides platform-wide analytics including total views, most popular content,
    and user engagement metrics.
    
    Args:
        current_admin: Currently logged-in admin user
        
    Returns:
        Dictionary with comprehensive analytics data
        
    Raises:
        403: If user is not an administrator
        500: If analytics calculation fails
    """
    try:
        # Get platform-wide trending content
        trending = AnalyticsService.get_trending_content(db=db, time_period="7d")
        
        # Could add more comprehensive admin analytics here
        # For now, return trending content as a starting point
        
        return {
            "trending_content": trending.dict(),
            "message": "Admin analytics overview retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve admin analytics: {str(e)}"
        )
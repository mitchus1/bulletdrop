"""
View Tracking Schemas

This module defines Pydantic schemas for view tracking API endpoints.
Handles validation and serialization for file views and profile views.

Classes:
    ViewCreate: Schema for creating view records
    FileViewResponse: Schema for file view data
    ProfileViewResponse: Schema for profile view data
    ViewAnalytics: Schema for aggregated view statistics
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class ViewCreate(BaseModel):
    """
    Schema for creating a new view record.
    
    This schema handles the common fields needed when recording
    any type of view (file or profile).
    """
    user_agent: Optional[str] = Field(None, max_length=500, description="Browser user agent string")
    referer: Optional[str] = Field(None, max_length=500, description="Referring URL")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileViewResponse(BaseModel):
    """
    Schema for file view response data.
    
    Returns view information for a specific file view record.
    """
    id: int
    upload_id: int
    viewer_ip: str
    user_agent: Optional[str]
    referer: Optional[str]
    country: Optional[str]
    viewed_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProfileViewResponse(BaseModel):
    """
    Schema for profile view response data.
    
    Returns view information for a specific profile view record.
    """
    id: int
    profile_user_id: int
    viewer_ip: str
    viewer_user_id: Optional[int]
    user_agent: Optional[str]
    referer: Optional[str]
    country: Optional[str]
    viewed_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ViewAnalytics(BaseModel):
    """
    Schema for aggregated view analytics data.
    
    Provides statistics and analytics for files or profiles.
    """
    content_id: int
    content_type: str  # 'file' or 'profile'
    total_views: int
    unique_viewers: int
    views_today: int
    views_this_week: int
    views_this_month: int
    recent_views: List[Dict[str, Any]] = Field(default_factory=list)
    top_countries: List[Dict[str, Any]] = Field(default_factory=list)
    hourly_distribution: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TrendingContent(BaseModel):
    """
    Schema for trending content analytics.
    
    Returns trending files and profiles based on view activity.
    """
    trending_files: List[Dict[str, Any]] = Field(default_factory=list)
    trending_profiles: List[Dict[str, Any]] = Field(default_factory=list)
    time_period: str = "24h"  # Time period for trending calculation
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ViewStatsResponse(BaseModel):
    """
    Schema for quick view statistics.
    
    Provides quick access to view counts and basic analytics.
    """
    total_views: int
    unique_viewers: Optional[int] = None
    last_viewed: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BulkViewCreate(BaseModel):
    """
    Schema for bulk view creation (for batch processing).
    
    Allows recording multiple views in a single API call for performance.
    """
    views: List[Dict[str, Any]]
    content_type: str  # 'file' or 'profile'
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
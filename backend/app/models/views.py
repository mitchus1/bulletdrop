"""
View Tracking Models

This module defines database models for tracking file views and profile views.
These models store analytics data for understanding content popularity and user engagement.

Classes:
    FileView: Track individual file/image views with IP and timestamp data
    ProfileView: Track profile page visits with visitor information
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class FileView(Base):
    """
    FileView database model for tracking file/image access analytics.
    
    This model records each time a file is viewed, including visitor information
    for analytics and usage tracking. Helps identify popular content and usage patterns.
    
    Attributes:
        id (int): Primary key, unique view record identifier
        upload_id (int): Foreign key to the Upload being viewed
        viewer_ip (str): IP address of the viewer (anonymized/hashed for privacy)
        user_agent (str, optional): Browser/client user agent string
        referer (str, optional): Referring URL that led to this view
        country (str, optional): Country code derived from IP (for geo analytics)
        viewed_at (datetime): Timestamp when the view occurred
        
    Relationships:
        upload: Many-to-one relationship with Upload model
    """
    __tablename__ = "file_views"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    viewer_ip = Column(String(45), nullable=False)  # Supports IPv4 and IPv6
    user_agent = Column(Text, nullable=True)
    referer = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)  # ISO country code
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    upload = relationship("Upload", back_populates="views")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_file_views_upload_time', 'upload_id', 'viewed_at'),
        Index('idx_file_views_ip_time', 'viewer_ip', 'viewed_at'),
    )


class ProfileView(Base):
    """
    ProfileView database model for tracking user profile page visits.
    
    This model records visits to user profile pages, helping understand
    user popularity and profile engagement metrics.
    
    Attributes:
        id (int): Primary key, unique view record identifier
        profile_user_id (int): Foreign key to the User whose profile was viewed
        viewer_ip (str): IP address of the viewer (anonymized/hashed for privacy)
        viewer_user_id (int, optional): Foreign key to logged-in viewer (if any)
        user_agent (str, optional): Browser/client user agent string
        referer (str, optional): Referring URL that led to this profile view
        country (str, optional): Country code derived from IP (for geo analytics)
        viewed_at (datetime): Timestamp when the profile was viewed
        
    Relationships:
        profile_user: Many-to-one relationship with User model (profile owner)
        viewer_user: Many-to-one relationship with User model (viewer, if logged in)
    """
    __tablename__ = "profile_views"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    viewer_ip = Column(String(45), nullable=False)  # Supports IPv4 and IPv6
    viewer_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    referer = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)  # ISO country code
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    profile_user = relationship("User", foreign_keys=[profile_user_id], back_populates="profile_views_received")
    viewer_user = relationship("User", foreign_keys=[viewer_user_id], back_populates="profile_views_made")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_profile_views_user_time', 'profile_user_id', 'viewed_at'),
        Index('idx_profile_views_ip_time', 'viewer_ip', 'viewed_at'),
    )


class ViewSummary(Base):
    """
    ViewSummary database model for storing aggregated view statistics.
    
    This model stores daily/hourly aggregated view data to improve performance
    of analytics queries and provide quick access to trending content.
    
    Attributes:
        id (int): Primary key, unique summary record identifier
        content_type (str): Type of content ('file' or 'profile')
        content_id (int): ID of the file/upload or user profile
        date (datetime): Date for this summary (truncated to day)
        view_count (int): Total views for this content on this date
        unique_viewers (int): Estimated unique viewers (by IP)
        
    Indexes:
        - content_type + content_id + date for fast lookup
        - date for trending queries
    """
    __tablename__ = "view_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(20), nullable=False)  # 'file' or 'profile'
    content_id = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False, index=True)  # Date truncated to day
    view_count = Column(Integer, default=0)
    unique_viewers = Column(Integer, default=0)

    # Composite indexes for fast queries
    __table_args__ = (
        Index('idx_view_summary_lookup', 'content_type', 'content_id', 'date'),
        Index('idx_view_summary_date', 'date', 'view_count'),
        {'extend_existing': True}
    )
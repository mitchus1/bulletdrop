"""
Upload Model Module

This module defines the Upload database model for the BulletDrop application.
The Upload model tracks all file uploads, their metadata, and access information.

Classes:
    Upload: SQLAlchemy model representing a file upload
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Upload(Base):
    """
    Upload database model representing a file upload in the BulletDrop platform.

    This model stores comprehensive information about uploaded files including
    file metadata, access URLs, analytics, and expiration settings.

    Attributes:
        id (int): Primary key, unique upload identifier
        user_id (int): Foreign key to User model, owner of the upload

        File Information:
        filename (str): Generated unique filename for storage
        original_filename (str): Original filename as uploaded by user
        file_size (int): File size in bytes
        mime_type (str): MIME type of the uploaded file
        file_hash (str, optional): SHA-256 hash for duplicate detection

        URLs and Access:
        upload_url (str): Public URL where the file can be accessed
        custom_name (str, optional): User-defined custom name for the file
        domain_id (int, optional): Foreign key to Domain model for custom domains

        Analytics and Settings:
        view_count (int): Number of times the file has been viewed
        is_public (bool): Whether the file is publicly accessible (default: True)

        Expiration:
        expires_at (datetime, optional): Timestamp when file expires and gets deleted

        Timestamps:
        created_at (datetime): Upload creation timestamp
        updated_at (datetime): Last modification timestamp

        Relationships:
        user: Many-to-one relationship with User model
        domain: Many-to-one relationship with Domain model
        analytics: One-to-many relationship with UploadAnalytic model
    """
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File information
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=True)  # SHA-256 for per-user deduplication
    
    # URLs and access
    upload_url = Column(Text, nullable=False)
    custom_name = Column(String(100), unique=True, nullable=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True)
    
    # Analytics and settings
    view_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="uploads")
    domain = relationship("Domain", back_populates="uploads")
    analytics = relationship("UploadAnalytic", back_populates="upload", cascade="all, delete-orphan")
    views = relationship("FileView", back_populates="upload", cascade="all, delete-orphan")
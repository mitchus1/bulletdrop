"""
User Model Module

This module defines the User database model for the BulletDrop application.
The User model stores user authentication, profile, and account information.

Classes:
    User: SQLAlchemy model representing a user account
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    """
    User database model representing a user account in the BulletDrop platform.

    This model stores comprehensive user information including authentication data,
    profile customization options, OAuth provider linkages, storage usage tracking,
    and account status information.

    Attributes:
        id (int): Primary key, unique user identifier
        username (str): Unique username for login and identification
        email (str): Unique email address for account recovery and notifications
        hashed_password (str): Bcrypt-hashed password for authentication

        Profile Information:
        discord_id (str, optional): Discord OAuth user ID for linked accounts
        google_id (str, optional): Google OAuth user ID for linked accounts
        github_id (str, optional): GitHub OAuth user ID for linked accounts
        avatar_url (str, optional): URL to user's profile avatar image
        bio (str, optional): User's profile biography/description

        Social Media Links:
        github_username (str, optional): GitHub username for profile display
        discord_username (str, optional): Discord username for profile display
        telegram_username (str, optional): Telegram username for profile display
        instagram_username (str, optional): Instagram username for profile display

        Profile Customization:
        background_image (str, optional): URL to custom background image
        background_color (str, optional): Hex color code for background
        favorite_song (str, optional): User's favorite song for profile

        Storage and Usage:
        custom_domain (str, optional): User's custom domain for file hosting
        storage_used (int): Current storage usage in bytes
        storage_limit (int): Maximum storage allowance in bytes (default: 1GB)
        upload_count (int): Total number of files uploaded

        Account Status:
        is_active (bool): Whether the account is active (default: True)
        is_admin (bool): Whether user has admin privileges (default: False)
        is_verified (bool): Whether email is verified (default: False)
        api_key (str, optional): Unique API key for external integrations

        Timestamps:
        created_at (datetime): Account creation timestamp
        updated_at (datetime): Last account modification timestamp
        last_login (datetime, optional): Last successful login timestamp

        Relationships:
        uploads: One-to-many relationship with Upload model
        user_domains: One-to-many relationship with UserDomain model
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    discord_id = Column(String(50), unique=True, nullable=True)
    google_id = Column(String(50), unique=True, nullable=True)
    github_id = Column(String(50), unique=True, nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)

    # Social media links
    github_username = Column(String(100), nullable=True)
    discord_username = Column(String(100), nullable=True)
    telegram_username = Column(String(100), nullable=True)
    instagram_username = Column(String(100), nullable=True)

    # Profile customization
    background_image = Column(Text, nullable=True)
    background_color = Column(String(7), nullable=True)  # hex color
    favorite_song = Column(Text, nullable=True)
    
    # Domain and storage
    custom_domain = Column(String(255), nullable=True)
    preferred_domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True)
    storage_used = Column(BigInteger, default=0)  # bytes
    storage_limit = Column(BigInteger, default=1073741824)  # 1GB default
    upload_count = Column(Integer, default=0)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Premium subscription
    is_premium = Column(Boolean, default=False)
    premium_expires_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)  # For Stripe integration
    stripe_subscription_id = Column(String(255), nullable=True)  # Stripe subscription ID
    subscription_id = Column(String(255), nullable=True)  # For future subscription management
    
    # API access
    api_key = Column(String(255), unique=True, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    uploads = relationship("Upload", back_populates="user", cascade="all, delete-orphan")
    user_domains = relationship("UserDomain", back_populates="user", cascade="all, delete-orphan")
    preferred_domain = relationship("Domain", foreign_keys=[preferred_domain_id])
    
    def has_active_premium(self) -> bool:
        """Check if user has active premium subscription"""
        if not self.is_premium:
            return False
        if self.premium_expires_at is None:
            return True  # Lifetime premium
        return datetime.utcnow() < self.premium_expires_at
    
    def is_premium_eligible_for_domain(self, domain) -> bool:
        """Check if user can access a premium domain"""
        if not domain.is_premium:
            return True  # Non-premium domains are available to everyone
        return self.is_admin or self.has_active_premium()
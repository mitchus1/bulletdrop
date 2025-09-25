from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Username must be 3-30 characters, alphanumeric, underscore or dash only"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters"
    )

    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v

    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        if len(v) < 3 or len(v) > 30:
            raise ValueError('Username must be 3-30 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores and dashes')
        return v.strip().lower()

class UserLogin(BaseModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Username or email"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password"
    )

    @validator('username')
    def validate_login_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Username/email cannot be empty')
        return v.strip().lower()

    @validator('password')
    def validate_login_password(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class OAuthCallback(BaseModel):
    code: str
    # Optional redirect URI used during the provider auth step; required by some providers (e.g., Google/Discord)
    redirect_uri: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    discord_id: Optional[str] = None
    google_id: Optional[str] = None
    github_id: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    github_username: Optional[str] = None
    discord_username: Optional[str] = None
    telegram_username: Optional[str] = None
    instagram_username: Optional[str] = None
    background_image: Optional[str] = None
    background_color: Optional[str] = None
    favorite_song: Optional[str] = None
    custom_domain: Optional[str] = None
    preferred_domain_id: Optional[int] = None
    storage_used: int
    storage_limit: Optional[int] = 1073741824  # 1GB default
    upload_count: Optional[int] = 0
    is_active: bool = True
    is_admin: bool = False
    is_verified: Optional[bool] = False
    is_premium: bool = False
    premium_expires_at: Optional[datetime] = None
    default_image_effect: Optional[str] = None
    matrix_effect_enabled: Optional[bool] = True
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
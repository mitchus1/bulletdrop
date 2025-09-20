from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class OAuthCallback(BaseModel):
    code: str

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
    storage_limit: int
    upload_count: int
    is_active: bool
    is_admin: bool
    is_verified: bool
    is_premium: bool = False
    premium_expires_at: Optional[datetime] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
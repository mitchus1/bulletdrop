from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# User management schemas
class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    is_verified: bool
    storage_used: int
    storage_limit: int
    upload_count: int
    custom_domain: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_verified: Optional[bool] = None
    storage_limit: Optional[int] = None

# Domain management schemas
class AdminDomainResponse(BaseModel):
    id: int
    domain_name: str
    display_name: Optional[str]
    description: Optional[str]
    is_available: bool
    is_premium: bool
    max_file_size: int
    created_at: datetime
    user_count: int = 0
    upload_count: int = 0

    class Config:
        from_attributes = True

class DomainCreateRequest(BaseModel):
    domain_name: str = Field(..., description="Domain name (e.g., img.example.com)")
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_available: bool = True
    is_premium: bool = False
    max_file_size: int = Field(default=10485760, description="Max file size in bytes")

class DomainUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_available: Optional[bool] = None
    is_premium: Optional[bool] = None
    max_file_size: Optional[int] = None

# Statistics schemas
class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    verified_users: int
    total_uploads: int
    total_storage_used: int
    total_domains: int
    available_domains: int
    premium_domains: int

class UserActivityStats(BaseModel):
    user_id: int
    username: str
    upload_count: int
    storage_used: int
    last_login: Optional[datetime]
    created_at: datetime

class DomainStats(BaseModel):
    domain_id: int
    domain_name: str
    upload_count: int
    user_count: int
    total_size: int

class RecentActivity(BaseModel):
    type: str  # "user_registered", "upload", "domain_created"
    description: str
    timestamp: datetime
    user_id: Optional[int] = None
    username: Optional[str] = None
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UploadCreate(BaseModel):
    original_filename: str
    custom_name: Optional[str] = None
    domain_id: Optional[int] = None
    is_public: bool = True
    expires_at: Optional[datetime] = None

class UploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    upload_url: str
    custom_name: Optional[str] = None
    domain_id: Optional[int] = None
    view_count: int
    is_public: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UploadListResponse(BaseModel):
    uploads: list[UploadResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class ShareXResponse(BaseModel):
    """Response format compatible with ShareX"""
    url: str
    thumbnail_url: Optional[str] = None
    deletion_url: Optional[str] = None
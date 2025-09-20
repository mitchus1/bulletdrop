from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user
from app.models import User
from app.schemas.auth import UserResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class UserUpdateRequest(BaseModel):
    bio: Optional[str] = None
    github_username: Optional[str] = None
    discord_username: Optional[str] = None
    telegram_username: Optional[str] = None
    instagram_username: Optional[str] = None
    background_image: Optional[str] = None
    background_color: Optional[str] = None
    favorite_song: Optional[str] = None
    preferred_domain_id: Optional[int] = None

@router.get("/{username}", response_model=UserResponse)
async def get_user_profile(username: str, db: Session = Depends(get_db)):
    """Get user profile by username."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    # Update only the fields that were provided
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile."""
    return current_user
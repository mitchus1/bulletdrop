from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
import secrets
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user, verify_password, get_password_hash
from app.models import User
from app.schemas.auth import UserResponse
from pydantic import BaseModel, EmailStr
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

class AccountUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class PasswordChangeRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str

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

@router.get("/me/oauth-status")
async def get_oauth_status(current_user: User = Depends(get_current_active_user)):
    """Check if user is an OAuth user."""
    is_oauth_user = any([
        current_user.discord_id,
        current_user.google_id,
        current_user.github_id
    ])
    
    oauth_providers = []
    if current_user.discord_id:
        oauth_providers.append("discord")
    if current_user.google_id:
        oauth_providers.append("google")
    if current_user.github_id:
        oauth_providers.append("github")
    
    # Check if user has a real password (not empty string)
    has_password = bool(current_user.hashed_password and current_user.hashed_password.strip())
    
    return {
        "is_oauth_user": is_oauth_user,
        "oauth_providers": oauth_providers,
        "has_password": has_password
    }

@router.put("/me/account", response_model=UserResponse)
async def update_account(
    account_update: AccountUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update account information (username, email)."""
    
    # Check if username is already taken (if being updated)
    if account_update.username and account_update.username != current_user.username:
        existing_user = db.query(User).filter(
            User.username == account_update.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Check if email is already taken (if being updated)  
    if account_update.email and account_update.email != current_user.email:
        existing_user = db.query(User).filter(
            User.email == account_update.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
    
    # Update fields
    for field, value in account_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    
    # Check if user is an OAuth user (has any OAuth provider ID)
    is_oauth_user = any([
        current_user.discord_id,
        current_user.google_id,
        current_user.github_id
    ])
    
    # Check if user has an existing password
    has_existing_password = bool(current_user.hashed_password and current_user.hashed_password.strip())
    
    # For OAuth users setting their first password, current password is not required
    # For regular users or OAuth users with existing password, current password is required
    if not is_oauth_user and not password_data.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is required"
        )
    
    if has_existing_password and not password_data.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is required"
        )
    
    # Verify current password if provided (for regular users or OAuth users who already have a password)
    if password_data.current_password:
        # Check if user actually has a password to verify against
        if not current_user.hashed_password or not current_user.hashed_password.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No current password set. You can set a new password directly."
            )
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
    
    # Validate new password
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    if is_oauth_user and not has_existing_password:
        return {"message": "Password set successfully"}
    else:
        return {"message": "Password changed successfully"}


@router.post("/me/api-key")
async def generate_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new API key for the current user. Replaces any existing key.
    """
    api_key = secrets.token_urlsafe(48)
    current_user.api_key = api_key
    db.commit()
    return {"api_key": api_key}


@router.delete("/me/api-key")
async def revoke_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoke the current user's API key.
    """
    current_user.api_key = None
    db.commit()
    return {"message": "API key revoked"}


@router.get("/me/api-key")
async def get_api_key(
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve whether the user has an API key. For security, only return presence flag unless explicitly requested.
    """
    return {"has_api_key": bool(current_user.api_key)}
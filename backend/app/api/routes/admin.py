from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from app.models.domain import Domain, UserDomain
from app.models.upload import Upload
from app.schemas.admin import (
    AdminUserResponse,
    UserUpdateRequest,
    AdminDomainResponse,
    DomainCreateRequest,
    DomainUpdateRequest,
    AdminStatsResponse,
    UserActivityStats,
    DomainStats,
    RecentActivity
)

router = APIRouter()

# User Management Endpoints
@router.get("/users", response_model=List[AdminUserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by username or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status")
):
    """Get all users with optional filtering"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Update user settings"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-demotion for admins
    if user.id == current_admin.id and user_update.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin privileges from yourself"
        )
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return {"message": "User updated successfully", "user": user}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete user account"""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user's uploads and related data
    db.query(Upload).filter(Upload.user_id == user_id).delete()
    db.query(UserDomain).filter(UserDomain.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

# Domain Management Endpoints
@router.get("/domains", response_model=List[AdminDomainResponse])
async def get_all_domains(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get all domains with usage statistics"""
    domains = db.query(
        Domain,
        func.count(UserDomain.id).label('user_count'),
        func.count(Upload.id).label('upload_count')
    ).outerjoin(UserDomain).outerjoin(Upload).group_by(Domain.id).all()
    
    result = []
    for domain, user_count, upload_count in domains:
        domain_dict = domain.__dict__.copy()
        domain_dict['user_count'] = user_count or 0
        domain_dict['upload_count'] = upload_count or 0
        result.append(AdminDomainResponse(**domain_dict))
    
    return result

@router.post("/domains", response_model=AdminDomainResponse)
async def create_domain(
    domain_data: DomainCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Create new domain"""
    # Check if domain already exists
    existing_domain = db.query(Domain).filter(Domain.domain_name == domain_data.domain_name).first()
    if existing_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain already exists"
        )
    
    domain = Domain(**domain_data.dict())
    db.add(domain)
    db.commit()
    db.refresh(domain)
    
    # Add usage statistics (will be 0 for new domain)
    domain_dict = domain.__dict__.copy()
    domain_dict['user_count'] = 0
    domain_dict['upload_count'] = 0
    
    return AdminDomainResponse(**domain_dict)

@router.patch("/domains/{domain_id}")
async def update_domain(
    domain_id: int,
    domain_update: DomainUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Update domain settings"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    update_data = domain_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(domain, field, value)
    
    db.commit()
    db.refresh(domain)
    
    return {"message": "Domain updated successfully", "domain": domain}

@router.delete("/domains/{domain_id}")
async def delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete domain"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    # Check if domain has uploads
    upload_count = db.query(Upload).filter(Upload.domain_id == domain_id).count()
    if upload_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete domain with {upload_count} uploads. Move or delete uploads first."
        )
    
    # Delete user domain associations
    db.query(UserDomain).filter(UserDomain.domain_id == domain_id).delete()
    db.delete(domain)
    db.commit()
    
    return {"message": "Domain deleted successfully"}

# Statistics Endpoints
@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get overall system statistics"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    total_uploads = db.query(Upload).count()
    total_storage_used = db.query(func.sum(User.storage_used)).scalar() or 0
    
    total_domains = db.query(Domain).count()
    available_domains = db.query(Domain).filter(Domain.is_available == True).count()
    premium_domains = db.query(Domain).filter(Domain.is_premium == True).count()
    
    return AdminStatsResponse(
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        verified_users=verified_users,
        total_uploads=total_uploads,
        total_storage_used=total_storage_used,
        total_domains=total_domains,
        available_domains=available_domains,
        premium_domains=premium_domains
    )

@router.get("/stats/users", response_model=List[UserActivityStats])
async def get_user_activity_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    limit: int = Query(50, ge=1, le=1000)
):
    """Get user activity statistics"""
    users = db.query(User).order_by(desc(User.upload_count)).limit(limit).all()
    
    return [
        UserActivityStats(
            user_id=user.id,
            username=user.username,
            upload_count=user.upload_count,
            storage_used=user.storage_used,
            last_login=user.last_login,
            created_at=user.created_at
        )
        for user in users
    ]

@router.get("/stats/domains", response_model=List[DomainStats])
async def get_domain_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get domain usage statistics"""
    domain_stats = db.query(
        Domain.id,
        Domain.domain_name,
        func.count(Upload.id).label('upload_count'),
        func.count(func.distinct(UserDomain.user_id)).label('user_count'),
        func.sum(Upload.file_size).label('total_size')
    ).outerjoin(Upload).outerjoin(UserDomain).group_by(Domain.id, Domain.domain_name).all()
    
    return [
        DomainStats(
            domain_id=stat.id,
            domain_name=stat.domain_name,
            upload_count=stat.upload_count or 0,
            user_count=stat.user_count or 0,
            total_size=stat.total_size or 0
        )
        for stat in domain_stats
    ]

@router.get("/activity", response_model=List[RecentActivity])
async def get_recent_activity(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get recent system activity"""
    since_date = datetime.utcnow() - timedelta(days=days)
    activities = []
    
    # Recent user registrations
    recent_users = db.query(User).filter(
        User.created_at >= since_date
    ).order_by(desc(User.created_at)).limit(limit // 3).all()
    
    for user in recent_users:
        activities.append(RecentActivity(
            type="user_registered",
            description=f"User '{user.username}' registered",
            timestamp=user.created_at,
            user_id=user.id,
            username=user.username
        ))
    
    # Recent uploads
    recent_uploads = db.query(Upload).filter(
        Upload.created_at >= since_date
    ).order_by(desc(Upload.created_at)).limit(limit // 3).all()
    
    for upload in recent_uploads:
        user = db.query(User).filter(User.id == upload.user_id).first()
        activities.append(RecentActivity(
            type="upload",
            description=f"File '{upload.original_filename}' uploaded",
            timestamp=upload.created_at,
            user_id=upload.user_id,
            username=user.username if user else "Unknown"
        ))
    
    # Recent domains (if any)
    recent_domains = db.query(Domain).filter(
        Domain.created_at >= since_date
    ).order_by(desc(Domain.created_at)).limit(limit // 3).all()
    
    for domain in recent_domains:
        activities.append(RecentActivity(
            type="domain_created",
            description=f"Domain '{domain.domain_name}' created",
            timestamp=domain.created_at
        ))
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    
    return activities[:limit]

# Premium Management Endpoints
@router.post("/users/{user_id}/premium")
async def grant_premium(
    user_id: int,
    months: int = 1,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Grant premium access to a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate expiration date
    if user.premium_expires_at and user.premium_expires_at > datetime.utcnow():
        # Extend existing premium
        expiration = user.premium_expires_at + timedelta(days=30 * months)
    else:
        # New premium subscription
        expiration = datetime.utcnow() + timedelta(days=30 * months)
    
    user.is_premium = True
    user.premium_expires_at = expiration
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"Premium granted to {user.username} until {expiration}",
        "user": user,
        "expires_at": expiration
    }

@router.delete("/users/{user_id}/premium")
async def revoke_premium(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Revoke premium access from a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_premium = False
    user.premium_expires_at = None
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"Premium access revoked from {user.username}",
        "user": user
    }
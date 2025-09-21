from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import json

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from app.models.domain import Domain, UserDomain
from app.models.upload import Upload
from app.services.stripe_service import StripeService
from app.services.redis_service import redis_service
from app.services.admin_monitoring import AdminMonitoringService
from app.api.routes import rate_limits

logger = logging.getLogger(__name__)
from app.schemas.admin import (
    AdminUserResponse,
    UserUpdateRequest,
    GrantPremiumRequest,
    SetStripeCustomerRequest,
    AdminDomainResponse,
    DomainCreateRequest,
    DomainUpdateRequest,
    AdminStatsResponse,
    UserActivityStats,
    DomainStats,
    RecentActivity
)

router = APIRouter()

# Include rate limiting admin routes
router.include_router(rate_limits.router, prefix="/rate-limits", tags=["rate-limits"])

# User Management Endpoints
@router.get("/users", response_model=List[AdminUserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by username or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    is_premium: Optional[bool] = Query(None, description="Filter by premium status")
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

    if is_premium is not None:
        query = query.filter(User.is_premium == is_premium)
    
    users = query.offset(skip).limit(limit).all()
    
    # Enhance users with oauth_providers field
    enhanced_users = []
    for user in users:
        user_dict = user.__dict__.copy()
        
        # Compute OAuth providers list
        oauth_providers = []
        if user.discord_id:
            oauth_providers.append("discord")
        if user.google_id:
            oauth_providers.append("google")
        if user.github_id:
            oauth_providers.append("github")
        
        user_dict['oauth_providers'] = oauth_providers
        enhanced_users.append(AdminUserResponse(**user_dict))
    
    return enhanced_users

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
    
    # Enhance user with oauth_providers field
    user_dict = user.__dict__.copy()
    
    # Compute OAuth providers list
    oauth_providers = []
    if user.discord_id:
        oauth_providers.append("discord")
    if user.google_id:
        oauth_providers.append("google")
    if user.github_id:
        oauth_providers.append("github")
    
    user_dict['oauth_providers'] = oauth_providers
    return AdminUserResponse(**user_dict)

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
    
    username = user.username
    email = user.email
    
    # Delete user's uploads and related data
    upload_count = db.query(Upload).filter(Upload.user_id == user_id).count()
    db.query(Upload).filter(Upload.user_id == user_id).delete()
    db.query(UserDomain).filter(UserDomain.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    
    return {
        "message": "User deleted successfully", 
        "deleted_user": {
            "username": username,
            "email": email,
            "uploads_deleted": upload_count
        }
    }

# Premium management
@router.post("/users/{user_id}/grant-premium")
async def grant_premium(
    user_id: int,
    payload: GrantPremiumRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Grant premium to a user. Supports lifetime, N days, or explicit expiry."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Determine expiry
    expires_at = None
    if payload.lifetime:
        expires_at = None
    elif payload.expires_at:
        expires_at = payload.expires_at
    elif payload.days and payload.days > 0:
        expires_at = datetime.utcnow() + timedelta(days=payload.days)

    user.is_premium = True
    user.premium_expires_at = expires_at
    db.commit()
    db.refresh(user)
    return {"message": "Premium granted", "user": AdminUserResponse(**user.__dict__, oauth_providers=[])}

@router.post("/users/{user_id}/revoke-premium")
async def revoke_premium(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Revoke premium from a user and clear Stripe subscription linkage."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_premium = False
    user.premium_expires_at = None
    # Do not touch customer id; clear subscription id to avoid stale linkage
    user.stripe_subscription_id = None
    db.commit()
    db.refresh(user)
    return {"message": "Premium revoked", "user": AdminUserResponse(**user.__dict__, oauth_providers=[])}

@router.post("/users/{user_id}/sync-stripe")
async def sync_user_from_stripe(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Sync user's premium from Stripe by finding an active/trialing subscription and updating fields."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.stripe_customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no Stripe customer id to sync")

    sub = StripeService.find_active_subscription_for_customer(user.stripe_customer_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active or trialing subscription found for this customer")

    # Update linkage and premium flags
    user.stripe_subscription_id = sub.get("id")
    StripeService.update_user_premium_status(db, user, sub)
    return {"message": "User synced from Stripe", "subscription_status": sub.get("status"), "user": AdminUserResponse(**user.__dict__, oauth_providers=[])}

@router.post("/users/{user_id}/set-stripe-customer")
async def set_user_stripe_customer(
    user_id: int,
    payload: SetStripeCustomerRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Set user's Stripe customer ID after validating it belongs to that user via metadata.user_id unless force=true."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    customer = StripeService.get_customer(payload.stripe_customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stripe customer not found")

    # Validate metadata.user_id if not forced
    if not payload.force:
        meta = (customer.get("metadata") or {})
        meta_uid = meta.get("user_id")
        if str(user.id) != str(meta_uid):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stripe customer metadata user_id mismatch; use force to override")

    user.stripe_customer_id = payload.stripe_customer_id
    db.commit()
    db.refresh(user)
    return {"message": "Stripe customer set", "user": AdminUserResponse(**user.__dict__, oauth_providers=[])}

@router.get("/statistics")
async def get_admin_statistics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get comprehensive admin statistics"""
    
    # Basic counts
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    premium_users = db.query(User).filter(User.is_premium == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    
    total_uploads = db.query(Upload).count()
    total_domains = db.query(Domain).count()
    
    # Storage statistics
    total_storage_used = db.query(func.sum(User.storage_used)).scalar() or 0
    avg_storage_per_user = total_storage_used / total_users if total_users > 0 else 0
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users_30d = db.query(User).filter(User.created_at >= thirty_days_ago).count()
    new_uploads_30d = db.query(Upload).filter(Upload.created_at >= thirty_days_ago).count()
    
    # Daily activity for last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_uploads = []
    daily_users = []
    
    for i in range(7):
        day_start = (datetime.utcnow() - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        uploads_count = db.query(Upload).filter(
            Upload.created_at >= day_start,
            Upload.created_at < day_end
        ).count()
        
        users_count = db.query(User).filter(
            User.created_at >= day_start,
            User.created_at < day_end
        ).count()
        
        daily_uploads.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": uploads_count
        })
        
        daily_users.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": users_count
        })
    
    # Top uploaders
    top_uploaders = db.query(
        User.username,
        User.email,
        User.is_premium,
        func.count(Upload.id).label('upload_count'),
        func.sum(Upload.file_size).label('total_size')
    ).join(Upload).group_by(User.id).order_by(desc(func.count(Upload.id))).limit(10).all()
    
    # Domain usage statistics
    domain_stats = db.query(
        Domain.domain_name,
        Domain.is_premium,
        func.count(Upload.id).label('upload_count')
    ).join(Upload, Upload.domain_id == Domain.id).group_by(Domain.id).order_by(desc(func.count(Upload.id))).all()
    
    return {
        "overview": {
            "total_users": total_users,
            "active_users": active_users,
            "premium_users": premium_users,
            "admin_users": admin_users,
            "total_uploads": total_uploads,
            "total_domains": total_domains,
            "total_storage_used": total_storage_used,
            "avg_storage_per_user": avg_storage_per_user
        },
        "recent_activity": {
            "new_users_30d": new_users_30d,
            "new_uploads_30d": new_uploads_30d
        },
        "daily_activity": {
            "uploads": daily_uploads,
            "users": daily_users
        },
        "top_uploaders": [
            {
                "username": username,
                "email": email,
                "is_premium": is_premium,
                "upload_count": count,
                "total_size": size or 0
            }
            for username, email, is_premium, count, size in top_uploaders
        ],
        "domain_usage": [
            {
                "domain_name": domain_name,
                "is_premium": is_premium,
                "upload_count": count
            }
            for domain_name, is_premium, count in domain_stats
        ]
    }

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
    """Get overall system statistics with Redis caching"""
    # Try to get cached stats first
    cache_key = "admin:stats:overview"
    cached_stats = redis_service._safe_operation(
        redis_service.redis_client.get, cache_key
    )

    if cached_stats:
        logger.debug("Using cached admin stats")
        return AdminStatsResponse(**json.loads(cached_stats))

    logger.debug("Computing fresh admin stats")

    # Compute expensive database aggregations
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()

    total_uploads = db.query(Upload).count()
    total_storage_used = float(db.query(func.sum(User.storage_used)).scalar() or 0)

    total_domains = db.query(Domain).count()
    available_domains = db.query(Domain).filter(Domain.is_available == True).count()
    premium_domains = db.query(Domain).filter(Domain.is_premium == True).count()

    stats_data = {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "verified_users": verified_users,
        "total_uploads": total_uploads,
        "total_storage_used": total_storage_used,
        "total_domains": total_domains,
        "available_domains": available_domains,
        "premium_domains": premium_domains
    }

    # Cache the results for 5 minutes
    redis_service._safe_operation(
        redis_service.redis_client.setex,
        cache_key,
        300,  # 5 minutes TTL
        json.dumps(stats_data)
    )

    return AdminStatsResponse(**stats_data)

@router.get("/stats/users", response_model=List[UserActivityStats])
async def get_user_activity_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    limit: int = Query(50, ge=1, le=1000)
):
    """Get user activity statistics with Redis caching"""
    # Create cache key based on limit parameter
    cache_key = f"admin:stats:users:{limit}"
    cached_stats = redis_service._safe_operation(
        redis_service.redis_client.get, cache_key
    )

    if cached_stats:
        logger.debug(f"Using cached user activity stats (limit={limit})")
        stats_list = json.loads(cached_stats)
        return [UserActivityStats(**stats) for stats in stats_list]

    logger.debug(f"Computing fresh user activity stats (limit={limit})")

    # Query top users by upload count
    users = db.query(User).order_by(desc(User.upload_count)).limit(limit).all()

    stats_list = []
    for user in users:
        stats_list.append({
            "user_id": user.id,
            "username": user.username,
            "upload_count": user.upload_count,
            "storage_used": user.storage_used,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat() if user.created_at else None
        })

    # Cache for 10 minutes
    redis_service._safe_operation(
        redis_service.redis_client.setex,
        cache_key,
        600,  # 10 minutes TTL
        json.dumps(stats_list, default=str)
    )

    return [UserActivityStats(**stats) for stats in stats_list]

@router.get("/stats/domains", response_model=List[DomainStats])
async def get_domain_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get domain usage statistics with Redis caching"""
    cache_key = "admin:stats:domains"
    cached_stats = redis_service._safe_operation(
        redis_service.redis_client.get, cache_key
    )

    if cached_stats:
        logger.debug("Using cached domain stats")
        stats_list = json.loads(cached_stats)
        return [DomainStats(**stats) for stats in stats_list]

    logger.debug("Computing fresh domain stats")

    # Expensive aggregation query
    domain_stats = db.query(
        Domain.id,
        Domain.domain_name,
        func.count(Upload.id).label('upload_count'),
        func.count(func.distinct(UserDomain.user_id)).label('user_count'),
        func.sum(Upload.file_size).label('total_size')
    ).outerjoin(Upload).outerjoin(UserDomain).group_by(Domain.id, Domain.domain_name).all()

    stats_list = []
    for stat in domain_stats:
        stats_list.append({
            "domain_id": stat.id,
            "domain_name": stat.domain_name,
            "upload_count": stat.upload_count or 0,
            "user_count": stat.user_count or 0,
            "total_size": stat.total_size or 0
        })

    # Cache for 15 minutes (domain stats change less frequently)
    redis_service._safe_operation(
        redis_service.redis_client.setex,
        cache_key,
        900,  # 15 minutes TTL
        json.dumps(stats_list)
    )

    return [DomainStats(**stats) for stats in stats_list]

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

# Advanced Monitoring Endpoints
@router.get("/monitoring/realtime")
async def get_realtime_metrics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get real-time platform metrics for admin monitoring dashboard"""
    try:
        metrics = AdminMonitoringService.get_realtime_metrics(db)
        return {"status": "success", "data": metrics}
    except Exception as e:
        logger.error(f"Error fetching realtime metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch realtime metrics"
        )

@router.get("/monitoring/activity-chart")
async def get_hourly_activity_chart(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to include (max 7 days)")
):
    """Get hourly activity data for charts"""
    try:
        chart_data = AdminMonitoringService.get_hourly_activity_chart(db, hours)
        return {"status": "success", "data": chart_data}
    except Exception as e:
        logger.error(f"Error fetching activity chart data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch activity chart data"
        )

@router.get("/monitoring/file-analytics")
async def get_file_upload_analytics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get comprehensive file upload analytics including sizes, types, and trends"""
    try:
        # Get upload metrics from the monitoring service
        realtime_metrics = AdminMonitoringService.get_realtime_metrics(db)
        upload_metrics = realtime_metrics.get("upload_metrics", {})

        # Add time-based analysis
        since_date = datetime.utcnow() - timedelta(days=days)
        recent_uploads = db.query(Upload).filter(Upload.created_at >= since_date).all()

        # File type analysis
        file_types = {}
        total_size = 0

        for upload in recent_uploads:
            ext = upload.original_filename.split('.')[-1].lower() if '.' in upload.original_filename else 'no_ext'
            if ext not in file_types:
                file_types[ext] = {"count": 0, "total_size": 0}
            file_types[ext]["count"] += 1
            file_types[ext]["total_size"] += upload.file_size or 0
            total_size += upload.file_size or 0

        # Sort file types by count
        sorted_file_types = sorted(file_types.items(), key=lambda x: x[1]["count"], reverse=True)

        analytics = {
            "period_summary": {
                "days_analyzed": days,
                "total_uploads": len(recent_uploads),
                "total_size": total_size,
                "average_size": total_size / len(recent_uploads) if recent_uploads else 0,
                "largest_file": max(recent_uploads, key=lambda x: x.file_size or 0).file_size if recent_uploads else 0
            },
            "file_types": [
                {
                    "extension": ext,
                    "count": data["count"],
                    "total_size": data["total_size"],
                    "percentage": (data["count"] / len(recent_uploads) * 100) if recent_uploads else 0
                }
                for ext, data in sorted_file_types[:10]  # Top 10 file types
            ],
            "size_distribution": upload_metrics.get("size_distribution", {}),
            "top_uploaders": upload_metrics.get("top_uploaders", [])
        }

        return {"status": "success", "data": analytics}
    except Exception as e:
        logger.error(f"Error fetching file analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch file analytics"
        )

@router.get("/monitoring/referral-tracking")
async def get_referral_tracking(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get comprehensive referral system tracking and analytics"""
    try:
        realtime_metrics = AdminMonitoringService.get_realtime_metrics(db)
        referral_metrics = realtime_metrics.get("referral_metrics", {})

        # Get top referrers with detailed stats
        top_referrers = db.query(
            User.id,
            User.username,
            User.email,
            User.referral_code,
            func.count(User.id).label('referral_count'),
            func.sum(User.storage_limit).label('bonus_awarded')
        ).join(
            User, User.referred_by == User.id, isouter=True
        ).filter(
            User.referral_code.isnot(None)
        ).group_by(
            User.id, User.username, User.email, User.referral_code
        ).order_by(
            desc(func.count(User.id))
        ).limit(20).all()

        referral_analytics = {
            "overview": referral_metrics,
            "top_referrers": [
                {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "referral_code": referral_code,
                    "total_referrals": referral_count or 0,
                    "bonus_awarded_mb": (bonus_awarded or 0) // (1024 * 1024)  # Convert to MB
                }
                for user_id, username, email, referral_code, referral_count, bonus_awarded in top_referrers
            ],
            "recent_referrals": referral_metrics.get("recent_activity", [])
        }

        return {"status": "success", "data": referral_analytics}
    except Exception as e:
        logger.error(f"Error fetching referral tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch referral tracking"
        )

@router.get("/monitoring/system-performance")
async def get_system_performance(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get system performance metrics including Redis and database stats"""
    try:
        realtime_metrics = AdminMonitoringService.get_realtime_metrics(db)
        performance_metrics = realtime_metrics.get("performance_metrics", {})

        # Additional database performance metrics
        db_stats = {
            "connection_count": 1,  # Would need actual connection pool monitoring
            "query_time_avg": "< 1ms",  # Would need query performance monitoring
            "active_sessions": 1
        }

        system_performance = {
            "redis": performance_metrics.get("redis", {}),
            "database": db_stats,
            "response_times": performance_metrics.get("response_times", {}),
            "cache_hit_rates": performance_metrics.get("cache_performance", {})
        }

        return {"status": "success", "data": system_performance}
    except Exception as e:
        logger.error(f"Error fetching system performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system performance"
        )

@router.get("/monitoring/view-analytics")
async def get_view_analytics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get detailed view analytics for files and profiles"""
    try:
        realtime_metrics = AdminMonitoringService.get_realtime_metrics(db)
        view_metrics = realtime_metrics.get("view_metrics", {})

        # Enhanced view analytics with time-based trends
        since_date = datetime.utcnow() - timedelta(days=days)

        # Get view trends from Redis if available
        view_trends = []
        for i in range(days):
            day = datetime.utcnow() - timedelta(days=i)
            day_key = day.strftime("%Y-%m-%d")

            # Try to get daily view counts from Redis
            daily_views = redis_service._safe_operation(
                redis_service.redis_client.get,
                f"daily_views:{day_key}"
            ) or 0

            view_trends.append({
                "date": day_key,
                "views": int(daily_views)
            })

        view_analytics = {
            "overview": view_metrics,
            "view_trends": sorted(view_trends, key=lambda x: x["date"]),
            "top_viewed_files": view_metrics.get("top_files", []),
            "top_viewed_profiles": view_metrics.get("top_profiles", [])
        }

        return {"status": "success", "data": view_analytics}
    except Exception as e:
        logger.error(f"Error fetching view analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch view analytics"
        )
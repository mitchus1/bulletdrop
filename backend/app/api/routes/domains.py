from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.domain import Domain, UserDomain

router = APIRouter()

class DomainCreateRequest(BaseModel):
    domain_name: str
    display_name: str
    description: str = ""
    is_available: bool = True
    is_premium: bool = False
    max_file_size: int = 10 * 1024 * 1024  # 10MB default

@router.get("/")
async def get_available_domains(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of available domains (filtered by user access level)"""
    domains = db.query(Domain).filter(Domain.is_available == True).all()
    
    # Filter domains based on user premium access
    accessible_domains = []
    for domain in domains:
        if current_user.is_premium_eligible_for_domain(domain):
            accessible_domains.append(domain)
    
    return {"domains": accessible_domains}

@router.post("/create")
async def create_domain(
    domain_data: DomainCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new domain (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if domain already exists
    existing_domain = db.query(Domain).filter(Domain.domain_name == domain_data.domain_name).first()
    if existing_domain:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Domain already exists"
        )
    
    # Create new domain
    new_domain = Domain(
        domain_name=domain_data.domain_name,
        display_name=domain_data.display_name,
        description=domain_data.description,
        is_available=domain_data.is_available,
        is_premium=domain_data.is_premium,
        max_file_size=domain_data.max_file_size
    )
    
    db.add(new_domain)
    db.commit()
    db.refresh(new_domain)
    
    return {"message": "Domain created successfully", "domain": new_domain}

class DomainUpdateRequest(BaseModel):
    display_name: str = None
    description: str = None
    is_available: bool = None
    is_premium: bool = None
    max_file_size: int = None

@router.patch("/{domain_id}")
async def update_domain(
    domain_id: int,
    domain_data: DomainUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a domain (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    # Update only provided fields
    update_data = domain_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(domain, field, value)
    
    db.commit()
    db.refresh(domain)
    
    return {"message": "Domain updated successfully", "domain": domain}

@router.delete("/{domain_id}")
async def delete_domain(
    domain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a domain (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    # Check if domain has uploads or users
    from app.models.upload import Upload
    uploads_count = db.query(Upload).filter(Upload.domain_id == domain_id).count()
    users_count = db.query(UserDomain).filter(UserDomain.domain_id == domain_id).count()
    
    if uploads_count > 0 or users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete domain with {uploads_count} uploads and {users_count} users"
        )
    
    db.delete(domain)
    db.commit()
    
    return {"message": "Domain deleted successfully"}

@router.post("/seed")
async def seed_domains(db: Session = Depends(get_db)):
    """Seed initial domains (development only)"""
    default_domains = [
        {
            "domain_name": "img.bulletdrop.com",
            "display_name": "Image Hosting",
            "description": "Primary image hosting domain",
            "is_available": True,
            "is_premium": False,
            "max_file_size": 10 * 1024 * 1024  # 10MB
        },
        {
            "domain_name": "shots.bulletdrop.com",
            "display_name": "Screenshots",
            "description": "Screenshots and quick captures",
            "is_available": True,
            "is_premium": False,
            "max_file_size": 5 * 1024 * 1024  # 5MB
        },
        {
            "domain_name": "cdn.bulletdrop.com",
            "display_name": "CDN",
            "description": "Content delivery network",
            "is_available": True,
            "is_premium": True,
            "max_file_size": 50 * 1024 * 1024  # 50MB
        },
        {
            "domain_name": "media.bulletdrop.com",
            "display_name": "Media Files",
            "description": "Large media file hosting",
            "is_available": True,
            "is_premium": True,
            "max_file_size": 100 * 1024 * 1024  # 100MB
        }
    ]

    created_count = 0
    for domain_data in default_domains:
        existing = db.query(Domain).filter(Domain.domain_name == domain_data["domain_name"]).first()
        if not existing:
            domain = Domain(**domain_data)
            db.add(domain)
            created_count += 1

    db.commit()
    return {"message": f"Created {created_count} domains"}

@router.post("/claim/{domain_id}")
async def claim_domain(
    domain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Claim a domain for the user"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )

    if not domain.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain not available"
        )

    # Check if user already claimed this domain
    existing_claim = db.query(UserDomain).filter(
        UserDomain.user_id == current_user.id,
        UserDomain.domain_id == domain_id
    ).first()

    if existing_claim:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Domain already claimed"
        )

    # Check if user can claim premium domains
    if domain.is_premium and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium domain requires admin privileges"
        )

    # Create user domain claim
    user_domain = UserDomain(
        user_id=current_user.id,
        domain_id=domain_id,
        is_primary=False  # User can set primary later
    )

    db.add(user_domain)
    db.commit()
    db.refresh(user_domain)

    return {
        "message": "Domain claimed successfully",
        "domain": domain,
        "claimed_at": user_domain.claimed_at
    }

@router.get("/my")
async def get_my_domains(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get domains claimed by current user"""
    user_domains = db.query(UserDomain).filter(
        UserDomain.user_id == current_user.id
    ).join(Domain).all()

    return {
        "domains": [
            {
                "id": ud.domain.id,
                "domain_name": ud.domain.domain_name,
                "display_name": ud.domain.display_name,
                "description": ud.domain.description,
                "is_primary": ud.is_primary,
                "claimed_at": ud.claimed_at,
                "max_file_size": ud.domain.max_file_size
            }
            for ud in user_domains
        ]
    }

@router.post("/my/{domain_id}/primary")
async def set_primary_domain(
    domain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Set a claimed domain as primary"""
    user_domain = db.query(UserDomain).filter(
        UserDomain.user_id == current_user.id,
        UserDomain.domain_id == domain_id
    ).first()

    if not user_domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not claimed by user"
        )

    # Unset all other domains as primary
    db.query(UserDomain).filter(
        UserDomain.user_id == current_user.id
    ).update({"is_primary": False})

    # Set this domain as primary
    user_domain.is_primary = True
    db.commit()

    return {"message": "Primary domain updated"}
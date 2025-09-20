from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.upload import Upload
from app.schemas.upload import UploadResponse, UploadListResponse, ShareXResponse
from app.services.upload_service import upload_service

router = APIRouter()

async def sync_user_counts(user: User, db: Session):
    """Automatically sync user upload counts to ensure accuracy"""
    from sqlalchemy import func
    
    # Get actual counts from uploads table
    result = db.query(
        func.count(Upload.id).label('upload_count'),
        func.coalesce(func.sum(Upload.file_size), 0).label('storage_used')
    ).filter(Upload.user_id == user.id).first()
    
    # Only update if counts are different (avoid unnecessary DB writes)
    if user.upload_count != result.upload_count or user.storage_used != result.storage_used:
        user.upload_count = result.upload_count
        user.storage_used = result.storage_used
        db.commit()

@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    custom_name: Optional[str] = Form(None),
    domain_id: Optional[int] = Form(None),
    is_public: bool = Form(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a file"""
    try:
        upload = await upload_service.upload_file(
            db=db,
            user=current_user,
            file=file,
            custom_name=custom_name,
            domain_id=domain_id,
            is_public=is_public
        )
        return upload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/sharex", response_model=ShareXResponse)
async def upload_file_sharex(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload endpoint compatible with ShareX and other screenshot tools"""
    try:
        upload = await upload_service.upload_file(
            db=db,
            user=current_user,
            file=file,
            is_public=True
        )

        return ShareXResponse(
            url=upload.upload_url,
            thumbnail_url=upload.upload_url if upload.mime_type.startswith('image/') else None,
            deletion_url=f"http://localhost:8000/api/uploads/{upload.id}/delete"  # TODO: Make configurable
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=UploadListResponse)
async def get_user_uploads(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of user uploads"""
    # Auto-sync user counts to ensure accuracy
    await sync_user_counts(current_user, db)
    
    result = upload_service.get_user_uploads(db, current_user, page, per_page)
    return result

@router.get("/{upload_id}", response_model=UploadResponse)
async def get_upload(
    upload_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific upload by ID"""
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.user_id == current_user.id
    ).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    return upload

@router.delete("/{upload_id}")
async def delete_upload(
    upload_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an upload"""
    success = upload_service.delete_upload(db, current_user, upload_id)

    if success:
        return {"message": "Upload deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete upload"
        )

@router.patch("/{upload_id}", response_model=UploadResponse)
async def update_upload(
    upload_id: int,
    custom_name: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update upload metadata"""
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.user_id == current_user.id
    ).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    if custom_name is not None:
        upload.custom_name = custom_name
    if is_public is not None:
        upload.is_public = is_public

    db.commit()
    db.refresh(upload)

    return upload

@router.post("/{upload_id}/view")
async def track_view(
    upload_id: int,
    db: Session = Depends(get_db)
):
    """Track file view (public endpoint)"""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()

    if not upload or not upload.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    upload.view_count += 1
    db.commit()

    return {"message": "View tracked"}

@router.post("/recalculate-counts")
async def recalculate_user_counts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    [DEPRECATED] Manually recalculate user's upload count and storage used from actual uploads.
    
    This endpoint is deprecated as upload counts and storage are now automatically 
    synchronized on every auth/me request and after each upload. The system now 
    maintains accurate counts automatically without manual intervention.
    """
    from sqlalchemy import func
    
    # Get actual counts from uploads table
    result = db.query(
        func.count(Upload.id).label('upload_count'),
        func.coalesce(func.sum(Upload.file_size), 0).label('storage_used')
    ).filter(Upload.user_id == current_user.id).first()
    
    # Update user with correct counts
    current_user.upload_count = result.upload_count
    current_user.storage_used = result.storage_used
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Counts recalculated (deprecated - now handled automatically)",
        "upload_count": current_user.upload_count,
        "storage_used": current_user.storage_used,
        "deprecated": True,
        "note": "Upload counts are now automatically synchronized. This endpoint will be removed in a future version."
    }
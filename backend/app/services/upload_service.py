import os
import uuid
import hashlib
import aiofiles
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from PIL import Image
import magic

from app.core.config import settings
from app.models.user import User
from app.models.upload import Upload
from app.models.domain import Domain

class UploadService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

        # Create subdirectories for organization
        (self.upload_dir / "images").mkdir(exist_ok=True)
        (self.upload_dir / "documents").mkdir(exist_ok=True)
        (self.upload_dir / "other").mkdir(exist_ok=True)

    def validate_file(self, file: UploadFile, user: User) -> dict:
        """Validate uploaded file"""
        # Check file size
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
            )

        # Check user storage quota
        if user.storage_used + (file.size or 0) > user.storage_limit:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Storage quota exceeded"
            )

        # Validate file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in settings.ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                )

        return {
            "original_filename": file.filename or "unknown",
            "file_size": file.size or 0,
            "file_extension": Path(file.filename or "").suffix.lower()
        }

    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename while preserving extension"""
        file_ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_ext}"

    def get_file_category(self, mime_type: str) -> str:
        """Determine file category for storage organization"""
        if mime_type.startswith('image/'):
            return 'images'
        elif mime_type.startswith(('application/', 'text/')):
            return 'documents'
        else:
            return 'other'

    async def save_file(self, file: UploadFile, filename: str, category: str) -> str:
        """Save file to disk and return relative path"""
        file_path = self.upload_dir / category / filename

        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)

            return str(Path(category) / filename)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for deduplication"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def detect_mime_type(self, file_path: Path) -> str:
        """Detect MIME type using python-magic"""
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(str(file_path))
        except:
            # Fallback to basic detection
            ext = file_path.suffix.lower()
            mime_map = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.webp': 'image/webp', '.pdf': 'application/pdf',
                '.txt': 'text/plain', '.md': 'text/markdown'
            }
            return mime_map.get(ext, 'application/octet-stream')

    def generate_upload_url(self, filename: str, domain: Optional[Domain] = None) -> str:
        """Generate public URL for uploaded file"""
        if domain:
            base_url = f"https://{domain.domain_name}"
        else:
            base_url = "http://localhost:8000"  # TODO: Make configurable

        return f"{base_url}/static/{filename}"

    async def create_upload_record(
        self,
        db: Session,
        user: User,
        file_info: dict,
        file_path: str,
        custom_name: Optional[str] = None,
        domain_id: Optional[int] = None,
        is_public: bool = True
    ) -> Upload:
        """Create upload record in database"""

        full_file_path = self.upload_dir / file_path
        file_hash = self.calculate_file_hash(full_file_path)
        mime_type = self.detect_mime_type(full_file_path)

        # Check for duplicate files
        existing_upload = db.query(Upload).filter(
            Upload.user_id == user.id,
            Upload.file_hash == file_hash
        ).first()

        if existing_upload:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="File already exists"
            )

        # Get domain if specified
        domain = None
        if domain_id:
            domain = db.query(Domain).filter(Domain.id == domain_id).first()
            if not domain or not domain.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or unavailable domain"
                )

        # Generate unique filename for URL
        unique_filename = self.generate_unique_filename(file_info["original_filename"])
        upload_url = self.generate_upload_url(file_path, domain)

        # Create upload record
        upload = Upload(
            user_id=user.id,
            filename=unique_filename,
            original_filename=file_info["original_filename"],
            file_size=file_info["file_size"],
            mime_type=mime_type,
            file_hash=file_hash,
            upload_url=upload_url,
            custom_name=custom_name,
            domain_id=domain_id,
            is_public=is_public
        )

        db.add(upload)

        # Update user storage and upload count atomically
        from sqlalchemy import text
        
        # Atomic increment of upload_count and storage_used
        db.execute(
            text("UPDATE users SET upload_count = upload_count + 1, storage_used = storage_used + :file_size WHERE id = :user_id"),
            {"file_size": file_info["file_size"], "user_id": user.id}
        )

        db.commit()
        db.refresh(upload)
        
        # Refresh user to get updated counts
        db.refresh(user)

        return upload

    async def upload_file(
        self,
        db: Session,
        user: User,
        file: UploadFile,
        custom_name: Optional[str] = None,
        domain_id: Optional[int] = None,
        is_public: bool = True
    ) -> Upload:
        """Complete file upload process"""

        # Validate file
        file_info = self.validate_file(file, user)

        # Generate unique filename
        unique_filename = self.generate_unique_filename(file_info["original_filename"])

        # Detect MIME type for categorization
        content = await file.read()
        await file.seek(0)  # Reset file pointer

        mime_type = magic.from_buffer(content[:1024], mime=True)
        category = self.get_file_category(mime_type)

        # Save file
        file_path = await self.save_file(file, unique_filename, category)

        # Create database record
        upload = await self.create_upload_record(
            db, user, file_info, file_path, custom_name, domain_id, is_public
        )

        return upload

    def get_user_uploads(
        self,
        db: Session,
        user: User,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Get paginated list of user uploads"""
        offset = (page - 1) * per_page

        query = db.query(Upload).filter(Upload.user_id == user.id)
        total = query.count()

        uploads = query.order_by(Upload.created_at.desc()).offset(offset).limit(per_page).all()

        return {
            "uploads": uploads,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": offset + per_page < total,
            "has_prev": page > 1
        }

    def delete_upload(self, db: Session, user: User, upload_id: int) -> bool:
        """Delete user upload"""
        upload = db.query(Upload).filter(
            Upload.id == upload_id,
            Upload.user_id == user.id
        ).first()

        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload not found"
            )

        # Delete file from disk
        try:
            file_path = self.upload_dir / upload.filename
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # Continue even if file deletion fails

        # Update user storage
        user.storage_used -= upload.file_size
        user.upload_count -= 1

        # Delete database record
        db.delete(upload)
        db.commit()

        return True

# Create service instance
upload_service = UploadService()
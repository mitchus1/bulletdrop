"""
BulletDrop API Main Application Module

This module serves as the entry point for the BulletDrop FastAPI application,
a Discord-style profile and image hosting platform with custom domain support.

The application provides:
- User authentication and management
- File upload and hosting capabilities
- Custom domain support for hosted files
- Admin panel for platform management
- RESTful API endpoints for all operations

Author: BulletDrop Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import uvicorn
from pathlib import Path
import io
from app.core.config import settings
from app.api.routes import auth, users, uploads, domains, admin, stripe, analytics, growth, landing, security
from app.core.database import engine, get_db
from app.models.upload import Upload
from app.core.database import Base
from app.services.analytics_service import AnalyticsService
from app.services.image_effects_service import ImageEffectsService
from app.schemas.analytics import ViewCreate
from app.middleware.rate_limit import RateLimitMiddleware
from sqlalchemy.orm import Session

# Create database tables on startup
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application with metadata
app = FastAPI(
    title="BulletDrop API",
    description="Discord profile and image hosting platform with custom domains",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware (before route handlers)
app.add_middleware(RateLimitMiddleware)

# Note: File serving is handled by the custom /uploads/{category}/{filename} endpoint
# This enables view tracking while preserving Discord embeds

# Include API route modules with appropriate prefixes and tags
app.include_router(auth.router, tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(domains.router, prefix="/api/domains", tags=["domains"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe"])
app.include_router(analytics.router, tags=["analytics"])
app.include_router(growth.router, prefix="/api/growth", tags=["growth"])
app.include_router(landing.router, prefix="/api/landing", tags=["landing"])
app.include_router(security.router, tags=["admin", "security"])





@app.get("/", summary="Root endpoint", description="Returns API status message")
async def root():
    """
    Root endpoint that confirms the API is running.

    Returns:
        dict: A simple message confirming the API status
    """
    return {"message": "BulletDrop API is running"}


@app.get("/health", summary="Health check", description="Returns API health status")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Health status information
    """
    return {"status": "healthy"}




@app.get("/uploads/{category}/{filename}")
async def serve_file_with_tracking(
    category: str,
    filename: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Serve uploaded files with view tracking.

    This endpoint replaces direct file serving to enable:
    - View tracking for analytics
    - Proper headers for embeds and ShareX compatibility
    - Proper headers for embeds and ShareX compatibility

    Query parameters: none
    """
    from app.services.redis_service import redis_service

    # Construct file path
    file_path = Path(settings.UPLOAD_DIR) / category / filename

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Try to get cached file metadata first (cache with category/filename format)
    full_filename = f"{category}/{filename}"
    cached_metadata = redis_service.get_cached_file_metadata(full_filename)

    if cached_metadata:
        # Use cached metadata
        upload_id = cached_metadata.get("id")
        is_public = cached_metadata.get("is_public", True)

        # Fast view counting with Redis
        if upload_id and is_public:
            redis_service.increment_file_view(upload_id)
    else:
        # Cache miss - get from database (database stores filename without category)
        upload_record = db.query(Upload).filter(
            Upload.filename == filename
        ).first()

        if upload_record:
            # Cache the metadata for future requests
            metadata = {
                "id": upload_record.id,
                "filename": upload_record.filename,
                "user_id": upload_record.user_id,
                "mime_type": upload_record.mime_type,
                "is_public": upload_record.is_public,
                "file_size": upload_record.file_size
            }
            redis_service.cache_file_metadata(full_filename, metadata)

            # Track view if file is public
            if upload_record.is_public:
                try:
                    # Fast Redis view count
                    redis_service.increment_file_view(upload_record.id)

                    # Also record detailed analytics (in background)
                    view_data = ViewCreate(
                        user_agent=request.headers.get("user-agent"),
                        referer=request.headers.get("referer")
                    )

                    AnalyticsService.record_file_view(
                        db=db,
                        upload_id=upload_record.id,
                        request=request,
                        view_data=view_data
                    )
                except Exception:
                    # Don't fail serving if tracking fails
                    pass

    # Effects are no longer applied at serve-time; handled at upload-time for premium users

    # Serve original file
    return FileResponse(
        path=file_path,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f"inline; filename={filename}",
        }
    )


if __name__ == "__main__":
    """
    Run the application using Uvicorn ASGI server.

    This is used for development purposes. In production, use a proper
    ASGI server like Gunicorn with Uvicorn workers.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)
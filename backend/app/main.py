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

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from app.core.config import settings
from app.api.routes import auth, users, uploads, domains, admin, stripe, analytics
from app.core.database import engine
from app.models import User, Upload, Domain
from app.core.database import Base

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

# Mount static files directory for serving uploaded content
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

# Include API route modules with appropriate prefixes and tags
app.include_router(auth.router, tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(domains.router, prefix="/api/domains", tags=["domains"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe"])
app.include_router(analytics.router, tags=["analytics"])


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

if __name__ == "__main__":
    """
    Run the application using Uvicorn ASGI server.

    This is used for development purposes. In production, use a proper
    ASGI server like Gunicorn with Uvicorn workers.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)
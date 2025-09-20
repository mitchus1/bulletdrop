from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/bulletdrop"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"

    # CORS
    ALLOWED_HOSTS: str = "http://localhost:3000,http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # File Upload
    UPLOAD_DIR: str = "/mnt/bulletdrop-storage/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_ALLOWED_TYPES: str = "image/jpeg,image/png,image/gif,image/webp"
    
    # Custom Domains
    AVAILABLE_DOMAINS: List[str] = [
        "img.bulletdrop.com",
        "shots.bulletdrop.com",
        "cdn.bulletdrop.com",
        "media.bulletdrop.com"
    ]

    # OAuth Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = ""
    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_REDIRECT_URI: str = ""

    # OAuth Redirect URLs
    FRONTEND_URL: str = "https://mitchus.me"
    
    # Base URL for file uploads (will be overridden by request host if not set)
    BASE_URL: str = ""
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()
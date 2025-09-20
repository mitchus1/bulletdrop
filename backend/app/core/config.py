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
    # Include local dev and production domains pointing to the same frontend
    ALLOWED_HOSTS: str = "http://localhost:3000,http://localhost:5173,https://mitchus.me,https://kitsune-chan.page"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://mitchus.me,https://kitsune-chan.page"
    
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

    # OAuth Redirect URLs (leave empty to use dynamic origin at runtime)
    FRONTEND_URL: str = ""
    
    # Base URL for file uploads (will be overridden by request host if not set)
    BASE_URL: str = ""
    
    # Stripe Settings
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID: str = ""  # Monthly subscription price ID
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        # Prefer CORS_ORIGINS if set; else fall back to ALLOWED_HOSTS
        raw = self.CORS_ORIGINS or self.ALLOWED_HOSTS
        items = [o.strip() for o in raw.split(",") if o.strip()]
        # Ensure FRONTEND_URL is included
        if self.FRONTEND_URL and self.FRONTEND_URL not in items:
            items.append(self.FRONTEND_URL)
        return items
    
    class Config:
        env_file = ".env"

settings = Settings()
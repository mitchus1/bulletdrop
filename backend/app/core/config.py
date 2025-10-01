from pydantic_settings import BaseSettings
from typing import List
import secrets
import sys

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/bulletdrop"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate SECRET_KEY in production
        if self.ENVIRONMENT == "production" and self.SECRET_KEY == "your-secret-key-change-this-in-production":
            print("ERROR: Default SECRET_KEY detected in production environment!", file=sys.stderr)
            print("Please set a secure SECRET_KEY in your .env file.", file=sys.stderr)
            print(f"You can generate one with: openssl rand -hex 32", file=sys.stderr)
            sys.exit(1)

    # CORS
    # Include local dev and production domains pointing to the same frontend
    ALLOWED_HOSTS: str = "http://localhost:3000,http://localhost:5173,https://mitchus.me,https://kitsune-chan.page"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://mitchus.me,https://kitsune-chan.page"
    
    # File Upload
    UPLOAD_DIR: str = "/mnt/bulletdrop-storage/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB (10 * BYTES_PER_MB)
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB (10 * BYTES_PER_MB)
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

    # Valkey/Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_USER_PROFILE: int = 5 * 60  # 5 minutes (5 * SECONDS_PER_MINUTE)
    CACHE_TTL_FILE_METADATA: int = 60 * 60  # 1 hour (SECONDS_PER_HOUR)
    CACHE_TTL_ANALYTICS: int = 10 * 60  # 10 minutes (10 * SECONDS_PER_MINUTE)
    CACHE_TTL_VIEW_COUNTS: int = 24 * 60 * 60  # 24 hours (SECONDS_PER_DAY)

    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5
    RATE_LIMIT_AUTH_PER_HOUR: int = 20
    RATE_LIMIT_API_PER_MINUTE: int = 60
    RATE_LIMIT_API_PER_HOUR: int = 1000
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 10
    RATE_LIMIT_UPLOAD_PER_HOUR: int = 100
    RATE_LIMIT_BLOCK_DURATION: int = 5 * 60  # 5 minutes (5 * SECONDS_PER_MINUTE)
    
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
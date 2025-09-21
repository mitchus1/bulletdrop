"""
Security Module

This module handles authentication, authorization, and password management
for the BulletDrop application. It provides JWT token creation and validation,
password hashing, and user authentication utilities.

Key Components:
- Password hashing using bcrypt
- JWT token creation and verification
- User authentication functions
- FastAPI dependency injection for auth
- Admin and active user decorators

Dependencies:
- passlib for password hashing
- python-jose for JWT handling
- FastAPI security utilities
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Union, Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)

# Initialize password context for bcrypt hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize HTTP Bearer token security scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against its bcrypt hash.

    Args:
        plain_password (str): The plain text password to verify
        hashed_password (str): The bcrypt hashed password to check against

    Returns:
        bool: True if the password matches the hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a bcrypt hash for the given password.

    Args:
        password (str): The plain text password to hash

    Returns:
        str: The bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """
    Create a JWT access token with the given data and expiration.

    Args:
        data (dict): The payload data to encode in the token
        expires_delta (timedelta, optional): Custom expiration time delta.
                                           Defaults to ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
        str: The encoded JWT token

    Example:
        >>> token = create_access_token({"sub": "username"})
        >>> # Returns a JWT token valid for the configured expiration time
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify a JWT token and return its payload if valid.

    Args:
        token (str): The JWT token to verify

    Returns:
        Optional[dict]: The token payload if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def get_user_by_username_cached(db: Session, username: str) -> Optional[User]:
    """
    Get user by username with Redis caching for performance.

    For now, disabled caching to avoid SQLAlchemy session issues.
    The database lookup is fast enough for most use cases.

    Args:
        db (Session): Database session
        username (str): Username to look up

    Returns:
        Optional[User]: User object if found, None otherwise
    """
    # For now, always use database lookup to avoid session issues
    logger.debug(f"Fetching user {username} from database")
    user = db.query(User).filter(User.username == username).first()

    # TODO: Implement proper session-aware caching later
    # if user:
    #     # Cache user data for future lookups
    #     pass

    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.

    Args:
        credentials (HTTPAuthorizationCredentials): The Bearer token from the Authorization header
        db (Session): Database session dependency

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: 401 if credentials are invalid or user not found
        HTTPException: 400 if user is inactive

    Example:
        >>> @app.get("/protected")
        >>> async def protected_route(user: User = Depends(get_current_user)):
        >>>     return {"user_id": user.id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = get_user_by_username_cached(db, username)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency to ensure the current user is active.

    Args:
        current_user (User): The current user from get_current_user dependency

    Returns:
        User: The active user object

    Raises:
        HTTPException: 400 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    FastAPI dependency to optionally get the current authenticated user from JWT token.
    
    Unlike get_current_user, this function returns None if no valid token is provided
    instead of raising an exception.

    Args:
        credentials (Optional[HTTPAuthorizationCredentials]): The Bearer token from the Authorization header (optional)
        db (Session): Database session dependency

    Returns:
        Optional[User]: The authenticated user object or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            return None

        username: str = payload.get("sub")
        if username is None:
            return None

        user = get_user_by_username_cached(db, username)
        if user is None or not user.is_active:
            return None

        return user

    except JWTError:
        return None


def get_current_user_with_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> User:
    """
    Auth dependency that accepts either a Bearer JWT or an X-API-Key header.

    Priority: If X-API-Key is present and valid, authenticate via API key. Otherwise fall back to JWT.
    """
    # Try API Key first if provided
    if x_api_key:
        user = db.query(User).filter(User.api_key == x_api_key).first()
        if user and user.is_active:
            return user

    # Fallback to JWT if provided
    if credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            username: str = payload.get("sub")
            if username:
                user = get_user_by_username_cached(db, username)
                if user and user.is_active:
                    return user

    # If neither works, raise
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (token or API key)",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_active_user_with_api_key(current_user: User = Depends(get_current_user_with_api_key)) -> User:
    """
    Ensure the current user (via API key or JWT) is active.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    FastAPI dependency to ensure the current user has admin privileges.

    Args:
        current_user (User): The current active user

    Returns:
        User: The admin user object

    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Alias for consistency with other routes
get_current_admin = get_current_admin_user


def authenticate_user(db: Session, username: str, password: str) -> Union[User, bool]:
    """
    Authenticate a user with username and password.

    Args:
        db (Session): Database session
        username (str): The username to authenticate
        password (str): The plain text password

    Returns:
        Union[User, bool]: User object if authentication successful, False otherwise

    Example:
        >>> user = authenticate_user(db, "john_doe", "mypassword")
        >>> if user:
        >>>     print(f"Authenticated user: {user.username}")
        >>> else:
        >>>     print("Authentication failed")
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False

    # If no stored hash (empty string or None), treat as no password set
    if not user.hashed_password:
        return False

    try:
        if not verify_password(password, user.hashed_password):
            return False
    except Exception:
        # If hash is invalid/corrupted, fail authentication gracefully
        return False

    return user
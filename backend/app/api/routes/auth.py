from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    authenticate_user,
    get_current_user,
    get_current_active_user
)
from app.models import User
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse, OAuthCallback
from app.core.config import settings
from app.services.oauth import oauth, get_google_user_info, get_github_user_info, get_discord_user_info
import secrets

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if email exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Check if username exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/json", response_model=Token)
async def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with JSON payload instead of form data."""
    user = authenticate_user(db, user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get current user information with caching."""
    from sqlalchemy import func
    from app.models.upload import Upload
    from app.services.redis_service import redis_service

    # Try to get cached user counts first
    cached_counts = redis_service.get_cached_user_counts(current_user.id)

    if cached_counts:
        # Use cached counts if available and recent (less than 5 minutes old)
        current_user.upload_count = cached_counts["upload_count"]
        current_user.storage_used = cached_counts["storage_used"]
    else:
        # Cache miss - get actual counts from uploads table
        result = db.query(
            func.count(Upload.id).label('upload_count'),
            func.coalesce(func.sum(Upload.file_size), 0).label('storage_used')
        ).filter(Upload.user_id == current_user.id).first()

        # Update user if counts are different (avoid unnecessary DB writes)
        if current_user.upload_count != result.upload_count or current_user.storage_used != result.storage_used:
            current_user.upload_count = result.upload_count
            current_user.storage_used = result.storage_used
            db.commit()
            db.refresh(current_user)

        # Cache the counts for future requests
        redis_service.cache_user_counts(
            current_user.id,
            current_user.upload_count,
            current_user.storage_used
        )

    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (token blacklisting would be implemented here in production)."""
    # In a production app, you would implement token blacklisting here
    # For now, we'll just return a success message
    return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh user's access token."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# OAuth Routes
@router.get("/auth/{provider}")
async def oauth_login(provider: str, request: Request, redirect_origin: str | None = None):
    """Initiate OAuth login with the specified provider."""
    if provider not in ['google', 'github', 'discord']:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

    # Determine origin (supports multi-domain)
    origin = redirect_origin or str(request.headers.get('origin') or "") or str(request.base_url).rstrip('/')
    # Fallback to configured frontend URL origin if needed
    if not origin:
        origin = settings.FRONTEND_URL.rstrip('/')

    # Construct redirect_uri on the fly using the origin
    # The frontend routes handle /auth/:provider/callback
    redirect_uri = f"{origin}/auth/{provider}/callback"

    # Preserve origin in state to recover on callback redirects (especially for GET-based flows)
    import secrets as _secrets
    state = _secrets.token_urlsafe(16) + "::" + origin

    # Build authorization URL manually for each provider
    if provider == 'google':
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=openid email profile&"
            f"response_type=code&"
            f"access_type=offline&"
            f"state={state}"
        )
    elif provider == 'github':
        auth_url = (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={settings.GITHUB_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=user:email&"
            f"state={state}"
        )
    elif provider == 'discord':
        auth_url = (
            f"https://discord.com/api/oauth2/authorize?"
            f"client_id={settings.DISCORD_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=identify email&"
            f"state={state}"
        )

    return RedirectResponse(url=auth_url)

"""
Backward-compatibility OAuth callback aliases

Some OAuth provider configurations may still be pointing to
"/auth/oauth/{provider}/callback" from a previous version. To avoid
"oauth_failed" errors due to redirect URI mismatches, we provide
aliases that forward to the current callback handlers.
"""

# Alias: GET /auth/oauth/{provider}/callback -> reuse GET handler
@router.get("/auth/oauth/{provider}/callback")
async def oauth_callback_get_alias(
    provider: str,
    code: str,
    request: Request,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    # Delegate to the primary GET callback handler
    return await oauth_callback_get(provider, code, state, request, db)

# Alias: POST /auth/oauth/{provider}/callback -> reuse POST handler
@router.post("/auth/oauth/{provider}/callback", response_model=Token)
async def oauth_callback_post_alias(
    provider: str,
    callback_data: OAuthCallback,
    db: Session = Depends(get_db),
):
    # Delegate to the primary POST callback handler
    return await oauth_callback(provider, callback_data, db)

@router.get("/auth/{provider}/callback")
async def oauth_callback_get(provider: str, code: str, request: Request, state: str | None = None, db: Session = Depends(get_db)):
    """Handle OAuth callback from provider (GET request with query params)."""
    # Determine target origin for building redirect_uri used in token exchange
    from app.schemas.auth import OAuthCallback
    target_origin = None
    if state and '::' in state:
        try:
            target_origin = state.split('::', 1)[1]
        except Exception:
            target_origin = None
    if not target_origin:
        # Fallback to request base URL origin
        # request.base_url like http://host:port/
        base = str(request.base_url).rstrip('/')
        target_origin = base or settings.FRONTEND_URL.rstrip('/')

    try:
        redirect_uri = f"{target_origin}/auth/{provider}/callback"
        callback_data = OAuthCallback(code=code, redirect_uri=redirect_uri)
        token_response = await oauth_callback(provider, callback_data, db)
        frontend_url = (target_origin or settings.FRONTEND_URL).rstrip('/')
        redirect_url = f"{frontend_url}/?token={token_response['access_token']}"
        return RedirectResponse(url=redirect_url)
    except Exception:
        # Redirect to frontend with error
        error_url = f"{(target_origin or settings.FRONTEND_URL).rstrip('/')}/login?error=oauth_failed"
        return RedirectResponse(url=error_url)

@router.post("/auth/{provider}/callback", response_model=Token)
async def oauth_callback(provider: str, callback_data: OAuthCallback, db: Session = Depends(get_db)):
    """Handle OAuth callback and create/login user."""
    code = callback_data.code
    if provider not in ['google', 'github', 'discord']:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

    try:
        import httpx

        # Exchange code for access token
        # Use provided dynamic redirect_uri when available, else fallback to env
        redirect_uri = callback_data.redirect_uri
        if not redirect_uri:
            if provider == 'google':
                redirect_uri = settings.GOOGLE_REDIRECT_URI
            elif provider == 'github':
                redirect_uri = settings.GITHUB_REDIRECT_URI
            elif provider == 'discord':
                redirect_uri = settings.DISCORD_REDIRECT_URI
            else:
                raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

        if provider == 'google':
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
        elif provider == 'github':
            token_url = "https://github.com/login/oauth/access_token"
            token_data = {
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                # GitHub supports redirect_uri optionally if it was used initially
                **({"redirect_uri": redirect_uri} if redirect_uri else {}),
            }
        elif provider == 'discord':
            token_url = "https://discord.com/api/oauth2/token"
            token_data = {
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            }

        async with httpx.AsyncClient() as client:
            headers = {"Accept": "application/json"}
            response = await client.post(token_url, data=token_data, headers=headers)

            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange code for token")

            token_response = response.json()
            access_token = token_response.get('access_token')

            if not access_token:
                raise HTTPException(status_code=400, detail="No access token received")

            # Get user info from OAuth provider
            if provider == 'google':
                user_info = await get_google_user_info(access_token)
                provider_id = user_info.get('id')
                email = user_info.get('email')
                username = user_info.get('name', '').replace(' ', '_').lower()
                avatar_url = user_info.get('picture')
            elif provider == 'github':
                user_info = await get_github_user_info(access_token)
                provider_id = str(user_info.get('id'))
                email = user_info.get('email')
                username = user_info.get('login', '').lower()
                avatar_url = user_info.get('avatar_url')
            elif provider == 'discord':
                user_info = await get_discord_user_info(access_token)
                provider_id = user_info.get('id')
                email = user_info.get('email')
                username = user_info.get('username', '').lower()
                avatar_url = f"https://cdn.discordapp.com/avatars/{provider_id}/{user_info.get('avatar')}.png" if user_info.get('avatar') else None

            if not provider_id or not email:
                raise HTTPException(status_code=400, detail="Failed to get required user information")

            # Check if user exists with this OAuth provider
            existing_user = None
            if provider == 'google':
                existing_user = db.query(User).filter(User.google_id == provider_id).first()
            elif provider == 'github':
                existing_user = db.query(User).filter(User.github_id == provider_id).first()
            elif provider == 'discord':
                existing_user = db.query(User).filter(User.discord_id == provider_id).first()

            if existing_user:
                # Update last login
                existing_user.last_login = datetime.utcnow()
                if avatar_url:
                    existing_user.avatar_url = avatar_url
                db.commit()
                user = existing_user
            else:
                # Check if user exists with this email
                existing_email_user = db.query(User).filter(User.email == email).first()
                if existing_email_user:
                    # Link OAuth account to existing user
                    if provider == 'google':
                        existing_email_user.google_id = provider_id
                    elif provider == 'github':
                        existing_email_user.github_id = provider_id
                    elif provider == 'discord':
                        existing_email_user.discord_id = provider_id

                    if avatar_url:
                        existing_email_user.avatar_url = avatar_url
                    existing_email_user.last_login = datetime.utcnow()
                    db.commit()
                    user = existing_email_user
                else:
                    # Create new user
                    # Make sure username is unique
                    base_username = username or f"{provider}_user"
                    final_username = base_username
                    counter = 1
                    while db.query(User).filter(User.username == final_username).first():
                        final_username = f"{base_username}_{counter}"
                        counter += 1

                    # OAuth users don't have a password initially - set to empty string
                    # They can set one later if they want password-based login
                    new_user = User(
                        username=final_username,
                        email=email,
                        hashed_password="",  # No password for OAuth users initially
                        avatar_url=avatar_url,
                        is_active=True,
                        is_verified=True  # OAuth users are pre-verified
                    )

                    # Set OAuth provider ID
                    if provider == 'google':
                        new_user.google_id = provider_id
                    elif provider == 'github':
                        new_user.github_id = provider_id
                    elif provider == 'discord':
                        new_user.discord_id = provider_id

                    db.add(new_user)
                    db.commit()
                    db.refresh(new_user)
                    user = new_user

            # Create JWT token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            jwt_token = create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires
            )

            return {"access_token": jwt_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {str(e)}")

@router.get("/callback/{provider}")
async def oauth_callback_get(provider: str, code: str, db: Session = Depends(get_db)):
    """Handle OAuth GET callback from OAuth providers like Google."""
    if provider not in ['google', 'github', 'discord']:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
    
    # Convert GET request to POST format and reuse the existing logic
    from app.schemas.auth import OAuthCallback
    callback_data = OAuthCallback(code=code)
    
    # Call the existing POST callback handler to get the token
    token_response = await oauth_callback(provider, callback_data, db)
    
    # Redirect to frontend with the token
    frontend_url = settings.FRONTEND_URL
    access_token = token_response["access_token"]
    
    # Redirect to frontend with token in URL parameters
    redirect_url = f"{frontend_url}?token={access_token}&auth=success"
    
    return RedirectResponse(url=redirect_url)
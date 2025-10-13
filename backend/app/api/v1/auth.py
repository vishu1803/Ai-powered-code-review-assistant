from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.api.dependencies.auth import get_db, get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token, 
    create_refresh_token,
    verify_refresh_token,
    verify_password, 
    get_password_hash
)
from app.models.database.user import User
from app.models.schemas.user import (
    User as UserSchema,
    UserCreate,
    Token,
    LoginRequest,
    RefreshTokenRequest,
    PasswordChangeRequest,
)
from app.services.user_service import UserService
from app.services.integration_service import OAuthService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=UserSchema)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Register a new user."""
    user_service = UserService(db)
    
    # Check if user already exists
    existing_user = await user_service.get_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_user = await user_service.get_by_username(user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = await user_service.create_user(user_create)
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Login with email/username and password."""
    user_service = UserService(db)
    
    # Try to authenticate with email first, then username
    user = await user_service.get_by_email(form_data.username)
    if not user:
        user = await user_service.get_by_username(form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    # Update last login
    await user_service.update_last_login(user.id)
    
    # Create tokens
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Refresh access token using refresh token."""
    user_id = verify_refresh_token(refresh_request.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_service = UserService(db)
    user = await user_service.get_by_id(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = create_refresh_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )

@router.post("/change-password")
async def change_password(
    password_change: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Change user password."""
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    user_service = UserService(db)
    await user_service.update_password(current_user.id, password_change.new_password)
    
    return {"message": "Password updated successfully"}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)) -> Any:
    """Logout user (client should discard tokens)."""
    return {"message": "Successfully logged out"}

# OAuth Endpoints
@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    """Initiate OAuth login with provider (github, gitlab)."""
    if provider not in ["github", "gitlab", "bitbucket"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )
    
    # OAuth URLs for different providers
    oauth_urls = {
        "github": f"https://github.com/login/oauth/authorize?client_id={getattr(settings, 'GITHUB_CLIENT_ID', '')}&scope=user:email,repo",
        "gitlab": f"https://gitlab.com/oauth/authorize?client_id={getattr(settings, 'GITLAB_CLIENT_ID', '')}&response_type=code&scope=read_user,read_repository",
        "bitbucket": f"https://bitbucket.org/site/oauth2/authorize?client_id={getattr(settings, 'BITBUCKET_CLIENT_ID', '')}&response_type=code"
    }
    
    if provider == "github" and not getattr(settings, 'GITHUB_CLIENT_ID', None):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured"
        )
    
    return {
        "provider": provider,
        "auth_url": oauth_urls.get(provider),
        "message": f"Redirect to {provider} for authentication"
    }

@router.post("/oauth/{provider}/callback", response_model=Token)
async def oauth_callback(
    provider: str,
    code: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Handle OAuth callback and create/login user."""
    if provider not in ["github", "gitlab", "bitbucket"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )
    
    try:
        # Exchange code for access token
        if provider == "github":
            access_token = await OAuthService.get_github_access_token(code)
        elif provider == "gitlab":
            access_token = await OAuthService.get_gitlab_access_token(code, "http://localhost:8000/oauth/callback")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth callback not implemented for {provider}"
            )
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from OAuth provider"
            )
        
        # Get user info from provider
        user_info = await OAuthService.get_user_info(provider, access_token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from OAuth provider"
            )
        
        # Create or update user
        user_service = UserService(db)
        user = await user_service.create_or_update_oauth_user(
            provider=provider,
            oauth_id=str(user_info["id"]),
            email=user_info["email"],
            username=user_info.get("login", user_info.get("username", f"{provider}_user_{user_info['id']}")),
            full_name=user_info.get("name"),
            avatar_url=user_info.get("avatar_url")
        )
        
        # Create tokens
        access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )

@router.get("/oauth/{provider}/status")
async def oauth_status(provider: str):
    """Get OAuth configuration status for provider."""
    if provider not in ["github", "gitlab", "bitbucket"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )
    
    config_status = {
        "provider": provider,
        "configured": False,
        "client_id": None
    }
    
    if provider == "github":
        github_client_id = getattr(settings, 'GITHUB_CLIENT_ID', None)
        github_client_secret = getattr(settings, 'GITHUB_CLIENT_SECRET', None)
        config_status["configured"] = bool(github_client_id and github_client_secret)
        config_status["client_id"] = github_client_id
    elif provider == "gitlab":
        gitlab_client_id = getattr(settings, 'GITLAB_CLIENT_ID', None)
        gitlab_client_secret = getattr(settings, 'GITLAB_CLIENT_SECRET', None)
        config_status["configured"] = bool(gitlab_client_id and gitlab_client_secret)
        config_status["client_id"] = gitlab_client_id
    elif provider == "bitbucket":
        bitbucket_client_id = getattr(settings, 'BITBUCKET_CLIENT_ID', None)
        bitbucket_client_secret = getattr(settings, 'BITBUCKET_CLIENT_SECRET', None)
        config_status["configured"] = bool(bitbucket_client_id and bitbucket_client_secret)
        config_status["client_id"] = bitbucket_client_id
    
    return config_status

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from app.core.config import settings
from app.core.logging import setup_logging
from app.models.database.base import async_engine
from app.api.v1.router import api_router
from app.api.middlewares.cors import setup_cors_middleware
from app.api.middlewares.logging import LoggingMiddleware
from app.api.middlewares.rate_limiting import RateLimitMiddleware
from app.api.dependencies.auth import get_db

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Code Review Assistant...")
    
    # Create database tables
    # Note: In production, use Alembic migrations instead
    if settings.ENVIRONMENT == "development":
        from app.models.database.base import Base
        async with async_engine.begin() as conn:  # Changed from 'engine' to 'async_engine'
            await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Code Review Assistant...")
    await async_engine.dispose()  # Changed from 'engine' to 'async_engine'
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "http_exception",
                "status_code": exc.status_code,
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "internal_error",
                "status_code": 500,
            }
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Code Review Assistant API",
        "version": settings.VERSION,
        "status": "running",
        "health": "/health",
        "api": {
            "docs": "/api/v1/docs",
            "redoc": "/api/v1/redoc", 
            "openapi": "/api/v1/openapi.json",
            "v1": "/api/v1/"
        },
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users", 
            "repositories": "/api/v1/repositories",
            "reviews": "/api/v1/reviews",
            "analytics": "/api/v1/analytics",
            "integrations": "/api/v1/integrations",
            "webhooks": "/api/v1/webhooks"
        }
    }

# OAuth callback handler for GitHub's URL format
@app.get("/api/auth/callback/{provider}")
async def oauth_callback_handler(
    provider: str,
    code: str,
    state: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth callback in GitHub's format."""
    if provider not in ["github", "gitlab", "bitbucket"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported OAuth provider"
        )
    
    try:
        # Import here to avoid circular imports
        from app.services.integration_service import OAuthService
        from app.services.user_service import UserService
        from app.core.security import create_access_token, create_refresh_token
        
        # Exchange code for access token
        if provider == "github":
            github_access_token = await OAuthService.get_github_access_token(code)
        elif provider == "gitlab":
            github_access_token = await OAuthService.get_gitlab_access_token(code, "http://localhost:8000/api/auth/callback/gitlab")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth callback not implemented for {provider}"
            )
        
        if not github_access_token:
            raise HTTPException(
                status_code=400,
                detail="Failed to get access token from OAuth provider"
            )
        
        # Get user info from provider
        user_info = await OAuthService.get_user_info(provider, github_access_token)
        if not user_info:
            raise HTTPException(
                status_code=400,
                detail="Failed to get user info from OAuth provider"
            )
        
        # Create or update user WITH GITHUB ACCESS TOKEN
        user_service = UserService(db)
        user = await user_service.create_or_update_oauth_user(
            provider=provider,
            oauth_id=str(user_info["id"]),
            email=user_info["email"],
            username=user_info.get("login", user_info.get("username", f"{provider}_user_{user_info['id']}")),
            full_name=user_info.get("name"),
            avatar_url=user_info.get("avatar_url"),
            github_access_token=github_access_token if provider == "github" else None
        )
        
        # Create JWT tokens
        access_token_jwt = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token_jwt = create_refresh_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        )
        
        # Redirect to frontend with tokens
        frontend_url = f"http://localhost:3000/auth/callback?access_token={access_token_jwt}&refresh_token={refresh_token_jwt}&provider={provider}&success=true"
        
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        # Redirect to frontend with error
        frontend_error_url = f"http://localhost:3000/auth/login?error=oauth_failed&provider={provider}&message={str(e)}"
        return RedirectResponse(url=frontend_error_url)

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )

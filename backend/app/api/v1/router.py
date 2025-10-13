from fastapi import APIRouter
from app.api.v1 import auth, users, repositories, reviews, analytics, integrations, webhooks

api_router = APIRouter()

# Root API endpoint (ADD THIS)
@api_router.get("/")
async def api_root():
    return {
        "message": "AI Code Review Assistant API v1",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "repositories": "/api/v1/repositories", 
            "reviews": "/api/v1/reviews",
            "analytics": "/api/v1/analytics",
            "integrations": "/api/v1/integrations",
            "webhooks": "/api/v1/webhooks",
            "health": "/api/v1/health"
        },
        "docs": {
            "swagger": "/api/v1/docs",
            "redoc": "/api/v1/redoc",
            "openapi": "/api/v1/openapi.json"
        }
    }

# Authentication routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# User management routes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# Repository management routes
api_router.include_router(
    repositories.router,
    prefix="/repositories",
    tags=["Repositories"]
)

# Code review routes
api_router.include_router(
    reviews.router,
    prefix="/reviews",
    tags=["Reviews"]
)

# Analytics and metrics routes
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

# VCS integrations routes
api_router.include_router(
    integrations.router,
    prefix="/integrations",
    tags=["Integrations"]
)

# Webhook handlers
api_router.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["Webhooks"]
)

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

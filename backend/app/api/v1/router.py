from fastapi import APIRouter
from app.api.v1 import auth, users, repositories, reviews, analytics, integrations, webhooks

api_router = APIRouter()

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
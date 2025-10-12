from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_db, get_current_user

router = APIRouter()

@router.get("/")
async def integrations_root():
    return {"message": "Integrations endpoints"}

@router.get("/github")
async def github_integration(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "GitHub integration - not implemented yet"}

@router.get("/gitlab")
async def gitlab_integration(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "GitLab integration - not implemented yet"}

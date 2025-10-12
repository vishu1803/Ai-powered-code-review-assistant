from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_db, get_current_user

router = APIRouter()

@router.get("/")
async def analytics_root():
    return {"message": "Analytics endpoints"}

@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Dashboard analytics - not implemented yet"}

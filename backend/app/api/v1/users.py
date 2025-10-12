from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_db, get_current_user

router = APIRouter()

@router.get("/")
async def users_root():
    return {"message": "Users endpoints"}

@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Current user info", "user": current_user}

@router.get("/list")
async def list_users(db: AsyncSession = Depends(get_db)):
    return {"message": "List users endpoint - not implemented yet"}

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.get("/")
async def webhooks_root():
    return {"message": "Webhooks endpoints"}

@router.post("/github")
async def github_webhook(request: Request):
    return {"message": "GitHub webhook received - not implemented yet"}

@router.post("/gitlab")
async def gitlab_webhook(request: Request):
    return {"message": "GitLab webhook received - not implemented yet"}

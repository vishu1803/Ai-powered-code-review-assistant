from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, get_current_user
from app.models.database.user import User
from app.models.schemas.repository import (
    Repository,
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryWithStats,
    ConnectRepositoryRequest,
    WebhookSetupRequest,
)
from app.services.repository_service import RepositoryService
from app.services.integration_service import IntegrationService
from app.workers.celery_tasks import setup_repository_analysis

router = APIRouter()


@router.get("/", response_model=List[Repository])
async def get_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    provider: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get user's repositories with filtering and pagination."""
    repository_service = RepositoryService(db)
    
    repositories = await repository_service.get_user_repositories(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search,
        provider=provider,
        is_active=is_active,
    )
    
    return repositories


@router.get("/{repository_id}", response_model=RepositoryWithStats)
async def get_repository(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get repository details with statistics."""
    repository_service = RepositoryService(db)
    
    repository = await repository_service.get_repository_with_stats(
        repository_id=repository_id,
        user_id=current_user.id,
    )
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    return repository


@router.post("/connect", response_model=Repository)
async def connect_repository(
    connect_request: ConnectRepositoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Connect a new repository from VCS provider."""
    integration_service = IntegrationService(db)
    
    # Validate repository access
    repo_info = await integration_service.validate_repository_access(
        provider=connect_request.provider,
        repository_url=connect_request.repository_url,
        access_token=connect_request.access_token,
        user_id=current_user.id,
    )
    
    # Create repository record
    repository_service = RepositoryService(db)
    repository_create = RepositoryCreate(
        name=repo_info["name"],
        full_name=repo_info["full_name"],
        description=repo_info.get("description"),
        url=repo_info["url"],
        clone_url=repo_info["clone_url"],
        default_branch=repo_info.get("default_branch", "main"),
        language=repo_info.get("language"),
        is_private=repo_info.get("is_private", False),
        provider=connect_request.provider,
        external_id=str(repo_info["id"]),
    )
    
    repository = await repository_service.create_repository(
        repository_create=repository_create,
        owner_id=current_user.id,
    )
    
    # Setup webhook
    webhook_url = f"{settings.BASE_URL}/api/v1/webhooks/{connect_request.provider}"
    webhook_id = await integration_service.setup_webhook(
        provider=connect_request.provider,
        repository_id=repository.external_id,
        webhook_url=webhook_url,
        access_token=connect_request.access_token,
    )
    
    if webhook_id:
        await repository_service.update_webhook_id(repository.id, webhook_id)
    
    # Start initial repository analysis
    setup_repository_analysis.delay(repository.id)
    
    return repository


@router.put("/{repository_id}", response_model=Repository)
async def update_repository(
    repository_id: int,
    repository_update: RepositoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update repository settings."""
    repository_service = RepositoryService(db)
    
    repository = await repository_service.get_by_id_and_owner(
        repository_id=repository_id,
        owner_id=current_user.id,
    )
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    updated_repository = await repository_service.update_repository(
        repository_id=repository_id,
        repository_update=repository_update,
    )
    
    return updated_repository


@router.delete("/{repository_id}")
async def delete_repository(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete repository connection."""
    repository_service = RepositoryService(db)
    
    repository = await repository_service.get_by_id_and_owner(
        repository_id=repository_id,
        owner_id=current_user.id,
    )
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Remove webhook if exists
    if repository.webhook_id:
        integration_service = IntegrationService(db)
        await integration_service.remove_webhook(
            provider=repository.provider,
            webhook_id=repository.webhook_id,
        )
    
    await repository_service.delete_repository(repository_id)
    
    return {"message": "Repository disconnected successfully"}


@router.post("/{repository_id}/analyze")
async def trigger_repository_analysis(
    repository_id: int,
    branch: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Trigger manual repository analysis."""
    repository_service = RepositoryService(db)
    
    repository = await repository_service.get_by_id_and_owner(
        repository_id=repository_id,
        owner_id=current_user.id,
    )
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    if not repository.analysis_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis is disabled for this repository"
        )
    
    # Start analysis task
    from app.workers.celery_tasks import analyze_repository
    task = analyze_repository.delay(repository_id, branch or repository.default_branch)
    
    return {
        "message": "Analysis started",
        "task_id": task.id,
        "repository_id": repository_id,
        "branch": branch or repository.default_branch,
    }


@router.get("/{repository_id}/branches")
async def get_repository_branches(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get repository branches."""
    repository_service = RepositoryService(db)
    
    repository = await repository_service.get_by_id_and_owner(
        repository_id=repository_id,
        owner_id=current_user.id,
    )
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    integration_service = IntegrationService(db)
    branches = await integration_service.get_repository_branches(
        provider=repository.provider,
        repository_id=repository.external_id,
    )
    
    return {"branches": branches}

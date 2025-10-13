from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

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
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

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

@router.get("/github/available")
async def get_available_github_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch available GitHub repositories for the current user."""
    if not current_user.github_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected. Please login with GitHub first."
        )
    
    integration_service = IntegrationService(db)
    
    try:
        # Fetch repositories from GitHub API
        github_repos = await integration_service.get_user_repositories(
            provider="github",
            user_id=current_user.id
        )
        
        # Get already connected repository external IDs
        repository_service = RepositoryService(db)
        connected_repos = await repository_service.get_user_repositories(
            user_id=current_user.id,
            provider="github"
        )
        connected_external_ids = {repo.external_id for repo in connected_repos if repo.external_id}
        
        # Mark which repositories are already connected
        for repo in github_repos:
            repo['is_connected'] = str(repo['id']) in connected_external_ids
        
        logger.info(f"Fetched {len(github_repos)} GitHub repositories for user {current_user.id}")
        return github_repos
        
    except Exception as e:
        logger.error(f"Error fetching GitHub repositories for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch GitHub repositories. Please try again."
        )

@router.post("/github/connect")
async def connect_github_repository(
    external_id: str = Query(..., description="GitHub repository ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Connect a specific GitHub repository by external ID."""
    if not current_user.github_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected"
        )
    
    integration_service = IntegrationService(db)
    repository_service = RepositoryService(db)
    
    try:
        # Check if repository is already connected
        existing_repo = await repository_service.get_by_external_id(
            external_id=external_id,
            provider="github",
            user_id=current_user.id
        )
        
        if existing_repo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository is already connected"
            )
        
        # Get repository details from GitHub API
        repo_info = await integration_service.get_repository_details(
            provider="github",
            repository_id=external_id,
            user_id=current_user.id
        )
        
        # Create repository record
        repository_create = RepositoryCreate(
            name=repo_info["name"],
            full_name=repo_info["full_name"],
            description=repo_info.get("description"),
            url=repo_info["html_url"],
            clone_url=repo_info["clone_url"],
            default_branch=repo_info.get("default_branch", "main"),
            language=repo_info.get("language"),
            is_private=repo_info.get("private", False),
            provider="github",
            external_id=str(repo_info["id"]),
            is_active=True,
            analysis_enabled=True
        )
        
        repository = await repository_service.create_repository(
            repository_create=repository_create,
            owner_id=current_user.id,
        )
        
        # Optional: Setup webhook (if integration service supports it)
        try:
            webhook_url = f"{settings.BASE_URL}/api/v1/webhooks/github"
            webhook_id = await integration_service.setup_webhook(
                provider="github",
                repository_id=repository.external_id,
                webhook_url=webhook_url,
                user_id=current_user.id,
            )
            
            if webhook_id:
                await repository_service.update_webhook_id(repository.id, webhook_id)
        except Exception as webhook_error:
            logger.warning(f"Failed to setup webhook for repository {repository.id}: {webhook_error}")
            # Continue without webhook - not critical for basic functionality
        
        # Optional: Start initial repository analysis
        try:
            setup_repository_analysis.delay(repository.id)
        except Exception as task_error:
            logger.warning(f"Failed to start initial analysis for repository {repository.id}: {task_error}")
            # Continue without initial analysis - user can manually trigger
        
        logger.info(f"Successfully connected GitHub repository {repo_info['full_name']} for user {current_user.id}")
        
        return {
            "message": "Repository connected successfully",
            "repository": repository
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting GitHub repository {external_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect repository. Please try again."
        )

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
    """Connect a new repository from VCS provider (generic endpoint)."""
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
        try:
            integration_service = IntegrationService(db)
            await integration_service.remove_webhook(
                provider=repository.provider,
                webhook_id=repository.webhook_id,
            )
        except Exception as e:
            logger.warning(f"Failed to remove webhook for repository {repository_id}: {e}")
    
    await repository_service.delete_repository(repository_id)
    
    logger.info(f"Repository {repository_id} disconnected by user {current_user.id}")
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
    try:
        from app.workers.celery_tasks import analyze_repository
        task = analyze_repository.delay(repository_id, branch or repository.default_branch)
        
        logger.info(f"Started analysis for repository {repository_id}, branch {branch or repository.default_branch}")
        
        return {
            "message": "Analysis started successfully",
            "task_id": task.id,
            "repository_id": repository_id,
            "branch": branch or repository.default_branch,
        }
    except Exception as e:
        logger.error(f"Failed to start analysis for repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start analysis. Please try again."
        )

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
    
    try:
        integration_service = IntegrationService(db)
        branches = await integration_service.get_repository_branches(
            provider=repository.provider,
            repository_id=repository.external_id,
            user_id=current_user.id
        )
        
        return {"branches": branches}
    except Exception as e:
        logger.error(f"Failed to fetch branches for repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch repository branches"
        )

@router.get("/{repository_id}/sync")
async def sync_repository(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Sync repository metadata from GitHub."""
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
    
    try:
        integration_service = IntegrationService(db)
        
        # Get updated repository info from GitHub
        repo_info = await integration_service.get_repository_details(
            provider=repository.provider,
            repository_id=repository.external_id,
            user_id=current_user.id
        )
        
        # Update repository metadata
        repository_update = RepositoryUpdate(
            name=repo_info["name"],
            full_name=repo_info["full_name"],
            description=repo_info.get("description"),
            url=repo_info["html_url"],
            default_branch=repo_info.get("default_branch", "main"),
            language=repo_info.get("language"),
            is_private=repo_info.get("private", False),
        )
        
        updated_repository = await repository_service.update_repository(
            repository_id=repository_id,
            repository_update=repository_update,
        )
        
        logger.info(f"Synced repository {repository_id} metadata")
        
        return {
            "message": "Repository synced successfully",
            "repository": updated_repository
        }
        
    except Exception as e:
        logger.error(f"Failed to sync repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync repository metadata"
        )

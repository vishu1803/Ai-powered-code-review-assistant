from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, get_current_user
from app.models.database.user import User
from app.models.schemas.review import (
    Review,
    ReviewCreate,
    ReviewUpdate,
    ReviewSummary,
    AnalysisRequest,
    AnalysisProgress,
    Issue,
    IssueUpdate,
    Comment,
    CommentCreate,
)
from app.services.review_service import ReviewService
from app.services.ai_analysis_service import AIAnalysisService
from app.workers.celery_tasks import analyze_code_changes, generate_review_summary

router = APIRouter()

@router.get("/", response_model=List[ReviewSummary])
async def get_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repository_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get user's code reviews with filtering and pagination."""
    review_service = ReviewService(db)
    
    reviews = await review_service.get_user_reviews(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        repository_id=repository_id,
        status=status,
    )
    
    return reviews

@router.get("/{review_id}", response_model=Review)
async def get_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get detailed review information."""
    review_service = ReviewService(db)
    
    review = await review_service.get_review_with_details(
        review_id=review_id,
        user_id=current_user.id,
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return review

# FIXED: Changed response_model to ReviewSummary instead of Review
@router.post("/", response_model=ReviewSummary)
async def create_review(
    review_create: ReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new code review."""
    review_service = ReviewService(db)
    
    try:
        # Verify repository access
        repository = await review_service.get_repository_by_id(review_create.repository_id)
        if not repository or repository.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Create review
        review = await review_service.create_review(
            review_create=review_create,
            author_id=current_user.id,
        )
        
        # Start analysis in background
        if repository.analysis_enabled:
            background_tasks.add_task(
                start_analysis_task,
                review.id,
                repository.id
            )
        
        # Return basic review data (ReviewSummary) without relationships
        return ReviewSummary(
            id=review.id,
            title=review.title,
            status=review.status,
            progress=review.progress,
            total_issues=review.total_issues,
            critical_issues=review.critical_issues,
            code_quality_score=review.code_quality_score,
            created_at=review.created_at,
            completed_at=review.completed_at,
            repository_id=review.repository_id,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating review: {e}")
        raise HTTPException(status_code=500, detail="Failed to create review")

# Helper function for background tasks
def start_analysis_task(review_id: int, repository_id: int):
    """Start analysis task in background"""
    try:
        analyze_code_changes.delay(
            review_id=review_id,
            repository_id=repository_id,
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error starting analysis task: {e}")

@router.put("/{review_id}", response_model=Review)
async def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update review information."""
    review_service = ReviewService(db)
    
    review = await review_service.get_review_by_id_and_author(
        review_id=review_id,
        author_id=current_user.id,
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    updated_review = await review_service.update_review(
        review_id=review_id,
        review_update=review_update,
    )
    
    return updated_review

@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete a review."""
    review_service = ReviewService(db)
    
    review = await review_service.get_review_by_id_and_author(
        review_id=review_id,
        author_id=current_user.id,
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    await review_service.delete_review(review_id)
    
    return {"message": "Review deleted successfully"}

# FIXED: Changed response to simple dict instead of complex model
@router.post("/analyze", response_model=dict)
async def start_code_analysis(
    analysis_request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Start AI-powered code analysis."""
    review_service = ReviewService(db)
    
    try:
        # Verify repository access
        repository = await review_service.get_repository_by_id(analysis_request.repository_id)
        if not repository or repository.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Create new review for analysis
        review_create = ReviewCreate(
            title=f"AI Analysis - {analysis_request.branch or repository.default_branch}",
            description="Automated AI-powered code analysis",
            repository_id=analysis_request.repository_id,
            source_branch=analysis_request.branch,
        )
        
        review = await review_service.create_review(
            review_create=review_create,
            author_id=current_user.id,
        )
        
        # Start analysis task
        try:
            task = analyze_code_changes.delay(
                review_id=review.id,
                repository_id=repository.id,
                commit_sha=analysis_request.commit_sha,
                files=analysis_request.files,
                rules=analysis_request.rules,
            )
            task_id = task.id
        except Exception:
            # If Celery is not available, return without task_id
            task_id = None
        
        return {
            "review_id": review.id,
            "task_id": task_id,
            "message": "Analysis started",
            "estimated_time": "2-5 minutes",
        }
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")

@router.get("/{review_id}/progress", response_model=AnalysisProgress)
async def get_analysis_progress(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get analysis progress for a review."""
    review_service = ReviewService(db)
    
    review = await review_service.get_review_by_id_and_author(
        review_id=review_id,
        author_id=current_user.id,
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    progress = await review_service.get_analysis_progress(review_id)
    return progress

@router.get("/{review_id}/issues", response_model=List[Issue])
async def get_review_issues(
    review_id: int,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    resolved: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get issues found in review."""
    review_service = ReviewService(db)
    
    # Verify review access
    review = await review_service.get_review_by_id_and_author(
        review_id=review_id,
        author_id=current_user.id,
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    issues = await review_service.get_review_issues(
        review_id=review_id,
        severity=severity,
        category=category,
        resolved=resolved,
    )
    
    return issues

@router.put("/issues/{issue_id}", response_model=Issue)
async def update_issue(
    issue_id: int,
    issue_update: IssueUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update issue status (resolve, mark as false positive)."""
    review_service = ReviewService(db)
    
    issue = await review_service.get_issue_by_id(issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Verify review ownership
    review = await review_service.get_review_by_id_and_author(
        review_id=issue.review_id,
        author_id=current_user.id,
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this issue"
        )
    
    updated_issue = await review_service.update_issue(
        issue_id=issue_id,
        issue_update=issue_update,
    )
    
    return updated_issue

@router.get("/{review_id}/comments", response_model=List[Comment])
async def get_review_comments(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get comments for a review."""
    review_service = ReviewService(db)
    
    # Verify review access
    review = await review_service.get_review_by_id_and_author(
        review_id=review_id,
        author_id=current_user.id,
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    comments = await review_service.get_review_comments(review_id)
    return comments

@router.post("/{review_id}/comments", response_model=Comment)
async def create_comment(
    review_id: int,
    comment_create: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Add comment to review."""
    review_service = ReviewService(db)
    
    # Verify review access
    review = await review_service.get_review_by_id_and_author(
        review_id=review_id,
        author_id=current_user.id,
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    comment = await review_service.create_comment(
        comment_create=comment_create,
        author_id=current_user.id,
        review_id=review_id,
    )
    
    return comment

@router.post("/{review_id}/summary")
async def generate_ai_summary(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Generate AI summary of review findings."""
    review_service = ReviewService(db)
    
    review = await review_service.get_review_by_id_and_author(
        review_id=review_id,
        author_id=current_user.id,
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Start summary generation task
    try:
        task = generate_review_summary.delay(review_id)
        task_id = task.id
    except Exception:
        # If Celery is not available, return without task_id
        task_id = None
    
    return {
        "message": "Summary generation started",
        "task_id": task_id,
        "review_id": review_id,
    }

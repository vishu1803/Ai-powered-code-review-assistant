from typing import List, Optional, Dict, Any
from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging

from app.workers.celery_app import celery_app
from app.models.database.base import async_session
from app.services.ai_analysis_service import AIAnalysisService
from app.services.repository_service import RepositoryService
from app.services.review_service import ReviewService
from app.services.git_service import GitService
from app.models.database.review import ReviewStatus

logger = logging.getLogger(__name__)


async def get_db_session() -> AsyncSession:
    """Get database session for async operations."""
    async with async_session() as session:
        return session


@celery_app.task(bind=True, name="analyze_code_changes")
def analyze_code_changes(
    self,
    review_id: int,
    repository_id: int,
    commit_sha: Optional[str] = None,
    files: Optional[List[str]] = None,
    rules: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Analyze code changes using AI."""
    try:
        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting analysis..."}
        )
        
        # Run async analysis
        result = asyncio.run(_analyze_code_changes_async(
            task=self,
            review_id=review_id,
            repository_id=repository_id,
            commit_sha=commit_sha,
            files=files,
            rules=rules,
        ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing code changes: {e}", exc_info=True)
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "traceback": str(e.__traceback__)}
        )
        raise


async def _analyze_code_changes_async(
    task,
    review_id: int,
    repository_id: int,
    commit_sha: Optional[str] = None,
    files: Optional[List[str]] = None,
    rules: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Async implementation of code analysis."""
    db = await get_db_session()
    
    try:
        # Initialize services
        review_service = ReviewService(db)
        repository_service = RepositoryService(db)
        ai_service = AIAnalysisService(db)
        git_service = GitService()
        
        # Get review and repository
        review = await review_service.get_by_id(review_id)
        repository = await repository_service.get_by_id(repository_id)
        
        if not review or not repository:
            raise ValueError("Review or repository not found")
        
        # Update review status
        await review_service.update_status(review_id, ReviewStatus.IN_PROGRESS)
        
        task.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Cloning repository..."}
        )
        
        # Clone or update repository
        repo_path = await git_service.prepare_repository(
            repository.clone_url,
            repository.default_branch,
            commit_sha
        )
        
        task.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Analyzing files..."}
        )
        
        # Get files to analyze
        if not files:
            files = await git_service.get_changed_files(repo_path, commit_sha)
        
        total_files = len(files)
        analyzed_files = 0
        issues_found = []
        
        # Update review with file counts
        await review_service.update_file_counts(review_id, total_files, 0)
        
        # Analyze each file
        for i, file_path in enumerate(files):
            try:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": 20 + (i * 60 // total_files),
                        "total": 100,
                        "status": f"Analyzing {file_path}..."
                    }
                )
                
                # Read file content
                file_content = await git_service.read_file(repo_path, file_path)
                
                # AI analysis
                file_issues = await ai_service.analyze_file(
                    file_path=file_path,
                    file_content=file_content,
                    repository=repository,
                    rules=rules,
                )
                
                # Save issues to database
                for issue_data in file_issues:
                    issue = await review_service.create_issue(
                        review_id=review_id,
                        issue_data=issue_data,
                    )
                    issues_found.append(issue)
                
                analyzed_files += 1
                await review_service.update_file_counts(review_id, total_files, analyzed_files)
                
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")
                continue
        
        task.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Generating quality scores..."}
        )
        
        # Calculate quality metrics
        quality_metrics = await ai_service.calculate_quality_metrics(
            repository_id=repository_id,
            issues=issues_found,
            total_files=total_files,
        )
        
        # Update review with results
        await review_service.update_analysis_results(
            review_id=review_id,
            quality_metrics=quality_metrics,
            total_issues=len(issues_found),
        )
        
        task.update_state(
            state="PROGRESS",
            meta={"current": 90, "total": 100, "status": "Finalizing analysis..."}
        )
        
        # Update review status to completed
        await review_service.update_status(review_id, ReviewStatus.COMPLETED)
        
        # Cleanup
        await git_service.cleanup_repository(repo_path)
        
        result = {
            "review_id": review_id,
            "total_files": total_files,
            "analyzed_files": analyzed_files,
            "total_issues": len(issues_found),
            "quality_score": quality_metrics.get("code_quality_score"),
            "security_score": quality_metrics.get("security_score"),
            "status": "completed",
        }
        
        task.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "result": result}
        )
        
        return result
        
    except Exception as e:
        await review_service.update_status(review_id, ReviewStatus.FAILED)
        raise
    finally:
        await db.close()


@celery_app.task(bind=True, name="generate_review_summary")
def generate_review_summary(self, review_id: int) -> Dict[str, Any]:
    """Generate AI summary of review findings."""
    try:
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Generating summary..."}
        )
        
        result = asyncio.run(_generate_review_summary_async(self, review_id))
        return result
        
    except Exception as e:
        logger.error(f"Error generating review summary: {e}", exc_info=True)
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise


async def _generate_review_summary_async(task, review_id: int) -> Dict[str, Any]:
    """Async implementation of summary generation."""
    db = await get_db_session()
    
    try:
        review_service = ReviewService(db)
        ai_service = AIAnalysisService(db)
        
        # Get review with issues
        review = await review_service.get_review_with_details(review_id)
        if not review:
            raise ValueError("Review not found")
        
        task.update_state(
            state="PROGRESS",
            meta={"current": 30, "total": 100, "status": "Analyzing issues..."}
        )
        
        # Generate AI summary
        summary_data = await ai_service.generate_review_summary(
            review=review,
            issues=review.issues,
        )
        
        task.update_state(
            state="PROGRESS",
            meta={"current": 70, "total": 100, "status": "Generating recommendations..."}
        )
        
        # Generate recommendations
        recommendations = await ai_service.generate_recommendations(
            review=review,
            issues=review.issues,
        )
        
        # Update review with summary
        await review_service.update_ai_summary(
            review_id=review_id,
            summary=summary_data["summary"],
            recommendations=recommendations,
        )
        
        result = {
            "review_id": review_id,
            "summary": summary_data["summary"],
            "recommendations": recommendations,
            "status": "completed",
        }
        
        task.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "result": result}
        )
        
        return result
        
    finally:
        await db.close()


@celery_app.task(bind=True, name="setup_repository_analysis")
def setup_repository_analysis(self, repository_id: int) -> Dict[str, Any]:
    """Setup initial repository analysis and indexing."""
    try:
        result = asyncio.run(_setup_repository_analysis_async(self, repository_id))
        return result
        
    except Exception as e:
        logger.error(f"Error setting up repository analysis: {e}", exc_info=True)
        raise


async def _setup_repository_analysis_async(task, repository_id: int) -> Dict[str, Any]:
    """Async implementation of repository setup."""
    db = await get_db_session()
    
    try:
        repository_service = RepositoryService(db)
        git_service = GitService()
        
        repository = await repository_service.get_by_id(repository_id)
        if not repository:
            raise ValueError("Repository not found")
        
        task.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Cloning repository..."}
        )
        
        # Clone repository
        repo_path = await git_service.prepare_repository(
            repository.clone_url,
            repository.default_branch,
        )
        
        task.update_state(
            state="PROGRESS",
            meta={"current": 60, "total": 100, "status": "Indexing repository..."}
        )
        
        # Get repository statistics
        stats = await git_service.get_repository_stats(repo_path)
        
        # Update repository information
        await repository_service.update_repository_stats(
            repository_id=repository_id,
            stats=stats,
        )
        
        # Cleanup
        await git_service.cleanup_repository(repo_path)
        
        return {
            "repository_id": repository_id,
            "status": "completed",
            "stats": stats,
        }
        
    finally:
        await db.close()

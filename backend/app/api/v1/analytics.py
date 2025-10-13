from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from app.api.dependencies.auth import get_db, get_current_user
from app.models.database.user import User
from app.models.database.repository import Repository
from app.models.database.review import Review
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def analytics_root():
    return {"message": "Analytics API - AI Code Review Assistant"}

@router.get("/overview")
async def get_overview_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive analytics overview for the current user."""
    try:
        # Get user's repositories
        user_repos_result = await db.execute(
            select(Repository).where(Repository.owner_id == current_user.id)
        )
        user_repositories = user_repos_result.scalars().all()
        repo_ids = [repo.id for repo in user_repositories]
        
        # If no repositories, return empty analytics
        if not repo_ids:
            return {
                "total_reviews": 0,
                "completed_reviews": 0,
                "total_issues_found": 0,
                "average_quality_score": 0.0,
                "average_security_score": 0.0,
                "average_performance_score": 0.0,
                "reviews_this_month": 0,
                "critical_issues": 0,
                "repositories_count": 0,
                "active_repositories": 0
            }
        
        # Get all reviews for user's repositories
        reviews_result = await db.execute(
            select(Review).where(Review.repository_id.in_(repo_ids))
        )
        all_reviews = reviews_result.scalars().all()
        
        # Calculate basic counts
        total_reviews = len(all_reviews)
        completed_reviews = [r for r in all_reviews if r.status == 'completed']
        completed_count = len(completed_reviews)
        
        # Calculate this month's reviews
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        reviews_this_month = len([r for r in all_reviews if r.created_at >= current_month])
        
        # Calculate average scores
        quality_scores = [r.code_quality_score for r in completed_reviews if r.code_quality_score is not None]
        security_scores = [r.security_score for r in completed_reviews if r.security_score is not None]
        performance_scores = [r.performance_score for r in completed_reviews if r.performance_score is not None]
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        avg_security = sum(security_scores) / len(security_scores) if security_scores else 0.0
        avg_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0.0
        
        # Calculate issues
        total_issues = sum(r.total_issues for r in completed_reviews if r.total_issues is not None)
        critical_issues = sum(r.critical_issues for r in completed_reviews if hasattr(r, 'critical_issues') and r.critical_issues is not None)
        
        # Repository stats
        active_repositories = len([repo for repo in user_repositories if repo.is_active and not repo.is_archived])
        
        analytics = {
            "total_reviews": total_reviews,
            "completed_reviews": completed_count,
            "total_issues_found": total_issues,
            "average_quality_score": round(avg_quality, 2),
            "average_security_score": round(avg_security, 2),
            "average_performance_score": round(avg_performance, 2),
            "reviews_this_month": reviews_this_month,
            "critical_issues": critical_issues if hasattr(Review, 'critical_issues') else 0,
            "repositories_count": len(user_repositories),
            "active_repositories": active_repositories
        }
        
        logger.info(f"Generated analytics overview for user {current_user.id}")
        return analytics
        
    except Exception as e:
        logger.error(f"Error generating analytics overview: {e}")
        # Return default analytics on error
        return {
            "total_reviews": 0,
            "completed_reviews": 0,
            "total_issues_found": 0,
            "average_quality_score": 0.0,
            "average_security_score": 0.0,
            "average_performance_score": 0.0,
            "reviews_this_month": 0,
            "critical_issues": 0,
            "repositories_count": 0,
            "active_repositories": 0
        }

@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get analytics for the dashboard view."""
    try:
        # Get basic overview
        overview = await get_overview_analytics(current_user, db)
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Get user's repositories
        user_repos_result = await db.execute(
            select(Repository).where(Repository.owner_id == current_user.id)
        )
        user_repositories = user_repos_result.scalars().all()
        repo_ids = [repo.id for repo in user_repositories]
        
        recent_reviews = []
        if repo_ids:
            recent_reviews_result = await db.execute(
                select(Review)
                .where(and_(
                    Review.repository_id.in_(repo_ids),
                    Review.created_at >= thirty_days_ago
                ))
                .order_by(desc(Review.created_at))
                .limit(10)
            )
            recent_reviews = recent_reviews_result.scalars().all()
        
        # Calculate trends
        weekly_reviews = len([r for r in recent_reviews if r.created_at >= datetime.now(timezone.utc) - timedelta(days=7)])
        
        dashboard_data = {
            **overview,
            "recent_activity": {
                "weekly_reviews": weekly_reviews,
                "recent_reviews": len(recent_reviews),
                "trend_direction": "up" if weekly_reviews > 0 else "stable"
            },
            "top_languages": await get_top_languages(current_user, db),
            "quality_trends": await get_quality_trends(current_user, db)
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error generating dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard analytics")

@router.get("/repositories")
async def get_repository_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get analytics specific to repositories."""
    try:
        # Get user's repositories with review counts
        repositories_result = await db.execute(
            select(Repository)
            .where(Repository.owner_id == current_user.id)
            .order_by(desc(Repository.updated_at))
        )
        repositories = repositories_result.scalars().all()
        
        repo_analytics = []
        for repo in repositories:
            # Get review count for this repository
            review_count_result = await db.execute(
                select(func.count(Review.id)).where(Review.repository_id == repo.id)
            )
            review_count = review_count_result.scalar() or 0
            
            # Get latest review
            latest_review_result = await db.execute(
                select(Review)
                .where(Review.repository_id == repo.id)
                .order_by(desc(Review.created_at))
                .limit(1)
            )
            latest_review = latest_review_result.scalar_one_or_none()
            
            repo_analytics.append({
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "provider": repo.provider,
                "language": repo.language,
                "is_active": repo.is_active,
                "total_reviews": review_count,
                "latest_review": latest_review.created_at.isoformat() if latest_review else None,
                "latest_review_status": latest_review.status if latest_review else None
            })
        
        return {
            "total_repositories": len(repositories),
            "active_repositories": len([r for r in repositories if r.is_active]),
            "repositories": repo_analytics
        }
        
    except Exception as e:
        logger.error(f"Error generating repository analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate repository analytics")

async def get_top_languages(current_user: User, db: AsyncSession) -> List[Dict[str, Any]]:
    """Get top programming languages by repository count."""
    try:
        # Get language distribution
        languages_result = await db.execute(
            select(Repository.language, func.count(Repository.id).label('count'))
            .where(Repository.owner_id == current_user.id)
            .group_by(Repository.language)
            .order_by(desc(func.count(Repository.id)))
            .limit(5)
        )
        languages = languages_result.all()
        
        return [
            {"language": lang.language or "Unknown", "count": lang.count}
            for lang in languages
        ]
    except Exception as e:
        logger.error(f"Error getting top languages: {e}")
        return []

async def get_quality_trends(current_user: User, db: AsyncSession) -> Dict[str, Any]:
    """Get quality score trends over time."""
    try:
        # Get user's repositories
        user_repos_result = await db.execute(
            select(Repository).where(Repository.owner_id == current_user.id)
        )
        user_repositories = user_repos_result.scalars().all()
        repo_ids = [repo.id for repo in user_repositories]
        
        if not repo_ids:
            return {"trend": "stable", "average_improvement": 0.0}
        
        # Get recent completed reviews with quality scores
        recent_reviews_result = await db.execute(
            select(Review.code_quality_score, Review.created_at)
            .where(and_(
                Review.repository_id.in_(repo_ids),
                Review.status == 'completed',
                Review.code_quality_score.isnot(None),
                Review.created_at >= datetime.now(timezone.utc) - timedelta(days=90)
            ))
            .order_by(Review.created_at)
        )
        recent_reviews = recent_reviews_result.all()
        
        if len(recent_reviews) < 2:
            return {"trend": "insufficient_data", "average_improvement": 0.0}
        
        # Calculate trend
        first_half = recent_reviews[:len(recent_reviews)//2]
        second_half = recent_reviews[len(recent_reviews)//2:]
        
        first_avg = sum(r.code_quality_score for r in first_half) / len(first_half)
        second_avg = sum(r.code_quality_score for r in second_half) / len(second_half)
        
        improvement = second_avg - first_avg
        
        trend = "improving" if improvement > 5 else "declining" if improvement < -5 else "stable"
        
        return {
            "trend": trend,
            "average_improvement": round(improvement, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating quality trends: {e}")
        return {"trend": "stable", "average_improvement": 0.0}

@router.get("/performance")
async def get_performance_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get performance-related analytics."""
    try:
        # Get user's repositories
        user_repos_result = await db.execute(
            select(Repository).where(Repository.owner_id == current_user.id)
        )
        user_repositories = user_repos_result.scalars().all()
        repo_ids = [repo.id for repo in user_repositories]
        
        if not repo_ids:
            return {
                "average_review_time": 0,
                "fastest_review": 0,
                "slowest_review": 0,
                "reviews_per_week": 0
            }
        
        # Get completed reviews
        completed_reviews_result = await db.execute(
            select(Review)
            .where(and_(
                Review.repository_id.in_(repo_ids),
                Review.status == 'completed'
            ))
        )
        completed_reviews = completed_reviews_result.scalars().all()
        
        if not completed_reviews:
            return {
                "average_review_time": 0,
                "fastest_review": 0,
                "slowest_review": 0,
                "reviews_per_week": 0
            }
        
        # Calculate review times (in hours)
        review_times = []
        for review in completed_reviews:
            if review.updated_at and review.created_at:
                duration = (review.updated_at - review.created_at).total_seconds() / 3600
                review_times.append(duration)
        
        avg_time = sum(review_times) / len(review_times) if review_times else 0
        fastest = min(review_times) if review_times else 0
        slowest = max(review_times) if review_times else 0
        
        # Reviews per week
        recent_reviews = [r for r in completed_reviews 
                         if r.created_at >= datetime.now(timezone.utc) - timedelta(days=7)]
        reviews_per_week = len(recent_reviews)
        
        return {
            "average_review_time": round(avg_time, 2),
            "fastest_review": round(fastest, 2),
            "slowest_review": round(slowest, 2),
            "reviews_per_week": reviews_per_week
        }
        
    except Exception as e:
        logger.error(f"Error generating performance analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate performance analytics")

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.database.repository import Repository
from app.models.database.user import User
from app.models.database.review import Review
from app.models.schemas.repository import RepositoryCreate, RepositoryUpdate

logger = logging.getLogger(__name__)

class RepositoryService:
    """Comprehensive repository management service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_repository(self, repository_create: RepositoryCreate, owner_id: int) -> Repository:
        """Create a new repository connection."""
        try:
            # Check if repository already exists for this user
            existing_repo = await self.db.execute(
                select(Repository).where(
                    and_(
                        Repository.external_id == repository_create.external_id,
                        Repository.provider == repository_create.provider,
                        Repository.owner_id == owner_id
                    )
                )
            )
            
            if existing_repo.scalar_one_or_none():
                raise ValueError("Repository already connected")
            
            # Create repository object
            repo_data = repository_create.dict()
            repo_data['owner_id'] = owner_id
            repo_data['review_rules'] = self._get_default_review_rules()
            repo_data['notification_settings'] = self._get_default_notification_settings()
            
            repository = Repository(**repo_data)
            
            self.db.add(repository)
            await self.db.commit()
            await self.db.refresh(repository)
            
            logger.info(f"Created repository: {repository.full_name} (ID: {repository.id})")
            return repository
            
        except ValueError:
            raise
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating repository: {e}")
            raise ValueError("Repository with this external ID already exists")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating repository: {e}")
            raise
    
    async def get_by_id(self, repository_id: int) -> Optional[Repository]:
        """Get repository by ID."""
        try:
            result = await self.db.execute(
                select(Repository).where(Repository.id == repository_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting repository by ID {repository_id}: {e}")
            return None
    
    async def get_by_id_and_owner(self, repository_id: int, owner_id: int) -> Optional[Repository]:
        """Get repository by ID and owner."""
        try:
            result = await self.db.execute(
                select(Repository).where(
                    and_(
                        Repository.id == repository_id,
                        Repository.owner_id == owner_id
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting repository by ID and owner: {e}")
            return None

    async def get_by_external_id(
        self,
        external_id: str,
        provider: str,
        user_id: int
    ) -> Optional[Repository]:
        """Get repository by external ID, provider, and user."""
        try:
            result = await self.db.execute(
                select(Repository).where(
                    and_(
                        Repository.external_id == external_id,
                        Repository.provider == provider,
                        Repository.owner_id == user_id
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting repository by external ID {external_id}: {e}")
            return None
    
    async def get_user_repositories(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        provider: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Repository]:
        """Get user's repositories with filtering."""
        try:
            query = select(Repository).where(Repository.owner_id == user_id)
            
            # Apply filters
            filters = []
            
            if search:
                search_pattern = f"%{search}%"
                filters.append(
                    or_(
                        Repository.name.ilike(search_pattern),
                        Repository.full_name.ilike(search_pattern),
                        Repository.description.ilike(search_pattern)
                    )
                )
            
            if provider:
                filters.append(Repository.provider == provider)
            
            if is_active is not None:
                filters.append(Repository.is_active == is_active)
            
            if filters:
                query = query.where(and_(*filters))
            
            # Order by last analysis or creation date
            query = query.order_by(desc(Repository.last_analysis), desc(Repository.created_at))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            repositories = result.scalars().all()
            
            return list(repositories)
            
        except Exception as e:
            logger.error(f"Error getting user repositories: {e}")
            return []
    
    async def get_repository_with_stats(self, repository_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get repository with comprehensive statistics."""
        try:
            # Get repository with reviews
            result = await self.db.execute(
                select(Repository)
                .options(selectinload(Repository.reviews))
                .where(
                    and_(
                        Repository.id == repository_id,
                        Repository.owner_id == user_id
                    )
                )
            )
            
            repository = result.scalar_one_or_none()
            if not repository:
                return None
            
            # Calculate statistics
            stats = await self._calculate_repository_stats(repository)
            
            # Get recent reviews
            recent_reviews = await self._get_recent_reviews(repository_id, limit=5)
            
            # Get quality trends
            quality_trend = await self._get_quality_trends(repository_id)
            
            repo_data = {
                'id': repository.id,
                'name': repository.name,
                'full_name': repository.full_name,
                'description': repository.description,
                'url': repository.url,
                'clone_url': repository.clone_url,
                'default_branch': repository.default_branch,
                'language': repository.language,
                'size': repository.size,
                'is_private': repository.is_private,
                'is_active': repository.is_active,
                'is_archived': repository.is_archived,
                'provider': repository.provider,
                'external_id': repository.external_id,
                'webhook_id': repository.webhook_id,
                'analysis_enabled': repository.analysis_enabled,
                'auto_review': repository.auto_review,
                'review_rules': repository.review_rules,
                'notification_settings': repository.notification_settings,
                'created_at': repository.created_at.isoformat(),
                'updated_at': repository.updated_at.isoformat() if repository.updated_at else None,
                'last_analysis': repository.last_analysis.isoformat() if repository.last_analysis else None,
                'stats': stats,
                'recent_reviews': recent_reviews,
                'quality_trend': quality_trend,
            }
            
            return repo_data
            
        except Exception as e:
            logger.error(f"Error getting repository with stats: {e}")
            return None
    
    async def update_repository(self, repository_id: int, repository_update: RepositoryUpdate) -> Optional[Repository]:
        """Update repository settings."""
        try:
            update_data = repository_update.dict(exclude_unset=True)
            if not update_data:
                return await self.get_by_id(repository_id)
            
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            await self.db.execute(
                update(Repository)
                .where(Repository.id == repository_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            updated_repository = await self.get_by_id(repository_id)
            logger.info(f"Updated repository: {repository_id}")
            return updated_repository
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating repository {repository_id}: {e}")
            raise
    
    async def update_webhook_id(self, repository_id: int, webhook_id: str) -> bool:
        """Update repository webhook ID."""
        try:
            await self.db.execute(
                update(Repository)
                .where(Repository.id == repository_id)
                .values(
                    webhook_id=webhook_id,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.commit()
            
            logger.info(f"Updated webhook ID for repository {repository_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating webhook ID for repository {repository_id}: {e}")
            return False
    
    async def update_repository_stats(self, repository_id: int, stats: Dict[str, Any]) -> bool:
        """Update repository statistics from Git analysis."""
        try:
            update_data = {
                'size': stats.get('total_files', 0),
                'language': stats.get('primary_language'),
                'last_analysis': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            await self.db.execute(
                update(Repository)
                .where(Repository.id == repository_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            logger.info(f"Updated repository stats for {repository_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating repository stats {repository_id}: {e}")
            return False
    
    async def delete_repository(self, repository_id: int) -> bool:
        """Delete repository connection (and associated reviews)."""
        try:
            # Note: In production, consider soft delete or archiving
            await self.db.execute(
                delete(Repository).where(Repository.id == repository_id)
            )
            await self.db.commit()
            
            logger.info(f"Deleted repository {repository_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting repository {repository_id}: {e}")
            return False
    
    async def _calculate_repository_stats(self, repository: Repository) -> Dict[str, Any]:
        """Calculate comprehensive repository statistics."""
        try:
            stats = {
                'total_reviews': len(repository.reviews) if repository.reviews else 0,
                'completed_reviews': 0,
                'pending_reviews': 0,
                'failed_reviews': 0,
                'average_quality_score': 0.0,
                'average_security_score': 0.0,
                'total_issues_found': 0,
                'critical_issues_found': 0,
                'last_review_date': None,
                'review_frequency': 0,
                'improvement_trend': 'stable',
            }
            
            if repository.reviews:
                completed_reviews = [r for r in repository.reviews if r.status == 'completed']
                pending_reviews = [r for r in repository.reviews if r.status in ['pending', 'in_progress']]
                failed_reviews = [r for r in repository.reviews if r.status == 'failed']
                
                stats['completed_reviews'] = len(completed_reviews)
                stats['pending_reviews'] = len(pending_reviews)
                stats['failed_reviews'] = len(failed_reviews)
                
                if completed_reviews:
                    # Calculate average scores
                    quality_scores = [r.code_quality_score for r in completed_reviews if r.code_quality_score]
                    security_scores = [r.security_score for r in completed_reviews if r.security_score]
                    
                    if quality_scores:
                        stats['average_quality_score'] = sum(quality_scores) / len(quality_scores)
                    
                    if security_scores:
                        stats['average_security_score'] = sum(security_scores) / len(security_scores)
                    
                    # Calculate issue statistics
                    stats['total_issues_found'] = sum(r.total_issues for r in completed_reviews)
                    stats['critical_issues_found'] = sum(r.critical_issues for r in completed_reviews)
                    
                    # Get last review date
                    latest_review = max(completed_reviews, key=lambda r: r.completed_at or r.created_at)
                    stats['last_review_date'] = (latest_review.completed_at or latest_review.created_at).isoformat()
                    
                    # Calculate review frequency (reviews per month)
                    if len(completed_reviews) > 1:
                        first_review = min(completed_reviews, key=lambda r: r.created_at)
                        last_review = max(completed_reviews, key=lambda r: r.created_at)
                        days_diff = (last_review.created_at - first_review.created_at).days
                        
                        if days_diff > 0:
                            stats['review_frequency'] = len(completed_reviews) / (days_diff / 30.0)
                    
                    # Calculate improvement trend
                    if len(completed_reviews) >= 3:
                        recent_reviews = sorted(completed_reviews, key=lambda r: r.created_at)[-3:]
                        if all(r.code_quality_score for r in recent_reviews):
                            scores = [r.code_quality_score for r in recent_reviews]
                            if scores[2] > scores[0]:
                                stats['improvement_trend'] = 'improving'
                            elif scores[2] < scores[0]:
                                stats['improvement_trend'] = 'declining'
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating repository stats: {e}")
            return {}
    
    async def _get_recent_reviews(self, repository_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent reviews for repository."""
        try:
            result = await self.db.execute(
                select(Review)
                .where(Review.repository_id == repository_id)
                .order_by(desc(Review.created_at))
                .limit(limit)
            )
            
            reviews = result.scalars().all()
            
            review_list = []
            for review in reviews:
                review_list.append({
                    'id': review.id,
                    'title': review.title,
                    'status': review.status.value,
                    'progress': review.progress,
                    'total_issues': review.total_issues,
                    'critical_issues': review.critical_issues,
                    'code_quality_score': review.code_quality_score,
                    'created_at': review.created_at.isoformat(),
                    'completed_at': review.completed_at.isoformat() if review.completed_at else None,
                })
            
            return review_list
            
        except Exception as e:
            logger.error(f"Error getting recent reviews: {e}")
            return []
    
    async def _get_quality_trends(self, repository_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get quality score trends over time."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            result = await self.db.execute(
                select(Review)
                .where(
                    and_(
                        Review.repository_id == repository_id,
                        Review.status == 'completed',
                        Review.completed_at >= cutoff_date,
                        Review.code_quality_score.isnot(None)
                    )
                )
                .order_by(Review.completed_at)
            )
            
            reviews = result.scalars().all()
            
            trend_data = []
            for review in reviews:
                trend_data.append({
                    'date': review.completed_at.isoformat(),
                    'quality_score': review.code_quality_score,
                    'security_score': review.security_score,
                    'total_issues': review.total_issues,
                    'critical_issues': review.critical_issues,
                })
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error getting quality trends: {e}")
            return []
    
    def _get_default_review_rules(self) -> Dict[str, Any]:
        """Get default review rules for new repositories."""
        return {
            'auto_review_enabled': True,
            'security_checks': True,
            'quality_checks': True,
            'performance_checks': True,
            'style_checks': False,
            'complexity_threshold': 10,
            'min_test_coverage': 80,
            'ignore_patterns': [
                '*.min.js',
                '*.min.css',
                'node_modules/*',
                '__pycache__/*',
                '.git/*',
                '*.log',
                '*.tmp',
            ],
            'custom_rules': [],
            'severity_thresholds': {
                'critical': 0,
                'high': 5,
                'medium': 20,
                'low': 50,
            }
        }
    
    def _get_default_notification_settings(self) -> Dict[str, Any]:
        """Get default notification settings for new repositories."""
        return {
            'email_on_review_complete': True,
            'email_on_critical_issues': True,
            'email_on_security_issues': True,
            'slack_notifications': False,
            'slack_webhook_url': None,
            'webhook_notifications': False,
            'webhook_url': None,
            'notify_on_improvement': True,
            'daily_summary': False,
            'weekly_summary': True,
        }

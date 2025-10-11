import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload

from app.models.database.review import Review, Issue, Comment, ReviewStatus, IssueSeverity
from app.models.database.repository import Repository
from app.models.database.user import User
from app.models.schemas.review import (
    ReviewCreate, ReviewUpdate, IssueCreate, IssueUpdate,
    CommentCreate, AnalysisProgress, ReviewSummary
)

logger = logging.getLogger(__name__)


class ReviewService:
    """Comprehensive code review management service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_review(self, review_create: ReviewCreate, author_id: int) -> Review:
        """Create a new code review."""
        try:
            # Verify repository exists and user has access
            repository = await self.get_repository_by_id(review_create.repository_id)
            if not repository or repository.owner_id != author_id:
                raise ValueError("Repository not found or access denied")
            
            # Create review object
            review_data = review_create.dict()
            review_data['author_id'] = author_id
            review_data['status'] = ReviewStatus.PENDING
            review_data['progress'] = 0.0
            review_data['analysis_metadata'] = {}
            review_data['ai_recommendations'] = []
            
            review = Review(**review_data)
            
            self.db.add(review)
            await self.db.commit()
            await self.db.refresh(review)
            
            logger.info(f"Created review: {review.title} (ID: {review.id})")
            return review
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating review: {e}")
            raise
    
    async def get_by_id(self, review_id: int) -> Optional[Review]:
        """Get review by ID."""
        try:
            result = await self.db.execute(
                select(Review).where(Review.id == review_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting review by ID {review_id}: {e}")
            return None
    
    async def get_review_by_id_and_author(self, review_id: int, author_id: int) -> Optional[Review]:
        """Get review by ID and author."""
        try:
            result = await self.db.execute(
                select(Review)
                .join(Repository)
                .where(
                    and_(
                        Review.id == review_id,
                        Repository.owner_id == author_id
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting review by ID and author: {e}")
            return None
    
    async def get_review_with_details(
        self, 
        review_id: int, 
        user_id: Optional[int] = None
    ) -> Optional[Review]:
        """Get review with all related data (issues, comments)."""
        try:
            query = (
                select(Review)
                .options(
                    selectinload(Review.issues),
                    selectinload(Review.comments).selectinload(Comment.author),
                    joinedload(Review.repository)
                )
                .where(Review.id == review_id)
            )
            
            # Add user access check if provided
            if user_id:
                query = query.join(Repository).where(Repository.owner_id == user_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting review with details: {e}")
            return None
    
    async def get_user_reviews(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        repository_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[ReviewSummary]:
        """Get user's reviews with filtering and pagination."""
        try:
            query = (
                select(Review)
                .join(Repository)
                .where(Repository.owner_id == user_id)
            )
            
            # Apply filters
            filters = []
            
            if repository_id:
                filters.append(Review.repository_id == repository_id)
            
            if status:
                try:
                    status_enum = ReviewStatus(status)
                    filters.append(Review.status == status_enum)
                except ValueError:
                    pass  # Invalid status, ignore filter
            
            if filters:
                query = query.where(and_(*filters))
            
            # Order by creation date (most recent first)
            query = query.order_by(desc(Review.created_at))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            reviews = result.scalars().all()
            
            # Convert to summary format
            review_summaries = []
            for review in reviews:
                summary = ReviewSummary(
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
                review_summaries.append(summary)
            
            return review_summaries
            
        except Exception as e:
            logger.error(f"Error getting user reviews: {e}")
            return []
    
    async def update_review(self, review_id: int, review_update: ReviewUpdate) -> Optional[Review]:
        """Update review information."""
        try:
            update_data = review_update.dict(exclude_unset=True)
            if not update_data:
                return await self.get_by_id(review_id)
            
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            await self.db.execute(
                update(Review)
                .where(Review.id == review_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            updated_review = await self.get_by_id(review_id)
            logger.info(f"Updated review: {review_id}")
            return updated_review
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating review {review_id}: {e}")
            raise
    
    async def update_status(self, review_id: int, status: ReviewStatus) -> bool:
        """Update review status."""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now(timezone.utc)
            }
            
            # Set completion timestamp if status is completed
            if status == ReviewStatus.COMPLETED:
                update_data['completed_at'] = datetime.now(timezone.utc)
                update_data['progress'] = 1.0
            
            await self.db.execute(
                update(Review)
                .where(Review.id == review_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            logger.info(f"Updated review {review_id} status to {status.value}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating review status {review_id}: {e}")
            return False
    
    async def update_progress(self, review_id: int, progress: float, current_file: Optional[str] = None) -> bool:
        """Update review analysis progress."""
        try:
            update_data = {
                'progress': max(0.0, min(1.0, progress)),  # Clamp between 0-1
                'updated_at': datetime.now(timezone.utc)
            }
            
            # Update metadata with current file being analyzed
            if current_file:
                review = await self.get_by_id(review_id)
                if review:
                    metadata = review.analysis_metadata or {}
                    metadata['current_file'] = current_file
                    metadata['last_update'] = datetime.now(timezone.utc).isoformat()
                    update_data['analysis_metadata'] = metadata
            
            await self.db.execute(
                update(Review)
                .where(Review.id == review_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating review progress {review_id}: {e}")
            return False
    
    async def update_file_counts(self, review_id: int, total_files: int, analyzed_files: int) -> bool:
        """Update file analysis counts."""
        try:
            await self.db.execute(
                update(Review)
                .where(Review.id == review_id)
                .values(
                    total_files=total_files,
                    analyzed_files=analyzed_files,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating file counts for review {review_id}: {e}")
            return False
    
    async def update_analysis_results(
        self,
        review_id: int,
        quality_metrics: Dict[str, Any],
        total_issues: int,
    ) -> bool:
        """Update review with analysis results."""
        try:
            update_data = {
                'total_issues': total_issues,
                'critical_issues': quality_metrics.get('critical_issues', 0),
                'high_issues': quality_metrics.get('high_issues', 0),
                'medium_issues': quality_metrics.get('medium_issues', 0),
                'low_issues': quality_metrics.get('low_issues', 0),
                'code_quality_score': quality_metrics.get('code_quality_score'),
                'security_score': quality_metrics.get('security_score'),
                'maintainability_score': quality_metrics.get('maintainability_score'),
                'updated_at': datetime.now(timezone.utc),
            }
            
            # Add test coverage if available
            if 'test_coverage' in quality_metrics:
                update_data['test_coverage'] = quality_metrics['test_coverage']
            
            await self.db.execute(
                update(Review)
                .where(Review.id == review_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            logger.info(f"Updated analysis results for review {review_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating analysis results for review {review_id}: {e}")
            return False
    
    async def update_ai_summary(
        self,
        review_id: int,
        summary: str,
        recommendations: List[Dict[str, Any]],
    ) -> bool:
        """Update review with AI-generated summary and recommendations."""
        try:
            await self.db.execute(
                update(Review)
                .where(Review.id == review_id)
                .values(
                    ai_summary=summary,
                    ai_recommendations=recommendations,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.commit()
            
            logger.info(f"Updated AI summary for review {review_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating AI summary for review {review_id}: {e}")
            return False
    
    async def delete_review(self, review_id: int) -> bool:
        """Delete a review and all associated data."""
        try:
            # This will cascade delete issues and comments due to foreign key constraints
            await self.db.execute(
                delete(Review).where(Review.id == review_id)
            )
            await self.db.commit()
            
            logger.info(f"Deleted review {review_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting review {review_id}: {e}")
            return False
    
    async def get_analysis_progress(self, review_id: int) -> AnalysisProgress:
        """Get current analysis progress for a review."""
        try:
            review = await self.get_by_id(review_id)
            if not review:
                raise ValueError("Review not found")
            
            # Calculate estimated time remaining
            estimated_time_remaining = None
            if review.progress > 0 and review.progress < 1.0:
                # Simple estimation based on current progress and elapsed time
                elapsed_time = (datetime.now(timezone.utc) - review.created_at).total_seconds()
                if elapsed_time > 0:
                    total_estimated_time = elapsed_time / review.progress
                    estimated_time_remaining = int(total_estimated_time - elapsed_time)
            
            # Get current file from metadata
            current_file = None
            if review.analysis_metadata:
                current_file = review.analysis_metadata.get('current_file')
            
            progress = AnalysisProgress(
                review_id=review.id,
                status=review.status,
                progress=review.progress,
                current_file=current_file,
                total_files=review.total_files,
                analyzed_files=review.analyzed_files,
                estimated_time_remaining=estimated_time_remaining,
            )
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting analysis progress for review {review_id}: {e}")
            raise
    
    # Issue Management Methods
    
    async def create_issue(self, review_id: int, issue_data: Dict[str, Any]) -> Issue:
        """Create a new issue for a review."""
        try:
            issue_create = IssueCreate(
                title=issue_data['title'],
                description=issue_data['description'],
                category=issue_data['category'],
                severity=issue_data['severity'],
                rule_id=issue_data.get('rule_id'),
                file_path=issue_data['file_path'],
                line_start=issue_data['line_start'],
                line_end=issue_data.get('line_end'),
                column_start=issue_data.get('column_start'),
                column_end=issue_data.get('column_end'),
                code_snippet=issue_data.get('code_snippet'),
                suggested_fix=issue_data.get('suggested_fix'),
                review_id=review_id,
                ai_explanation=issue_data.get('ai_explanation'),
                confidence_score=issue_data.get('confidence_score'),
            )
            
            issue = Issue(**issue_create.dict())
            
            self.db.add(issue)
            await self.db.commit()
            await self.db.refresh(issue)
            
            logger.debug(f"Created issue: {issue.title} for review {review_id}")
            return issue
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating issue for review {review_id}: {e}")
            raise
    
    async def get_issue_by_id(self, issue_id: int) -> Optional[Issue]:
        """Get issue by ID."""
        try:
            result = await self.db.execute(
                select(Issue).where(Issue.id == issue_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting issue by ID {issue_id}: {e}")
            return None
    
    async def get_review_issues(
        self,
        review_id: int,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[Issue]:
        """Get issues for a review with filtering."""
        try:
            query = select(Issue).where(Issue.review_id == review_id)
            
            # Apply filters
            filters = []
            
            if severity:
                try:
                    severity_enum = IssueSeverity(severity)
                    filters.append(Issue.severity == severity_enum)
                except ValueError:
                    pass  # Invalid severity, ignore filter
            
            if category:
                filters.append(Issue.category == category)
            
            if resolved is not None:
                filters.append(Issue.is_resolved == resolved)
            
            if filters:
                query = query.where(and_(*filters))
            
            # Order by severity (critical first), then by line number
            severity_order = {
                IssueSeverity.CRITICAL: 4,
                IssueSeverity.HIGH: 3,
                IssueSeverity.MEDIUM: 2,
                IssueSeverity.LOW: 1,
            }
            
            query = query.order_by(
                desc(Issue.severity),
                asc(Issue.file_path),
                asc(Issue.line_start)
            )
            
            result = await self.db.execute(query)
            issues = result.scalars().all()
            
            return list(issues)
            
        except Exception as e:
            logger.error(f"Error getting review issues: {e}")
            return []
    
    async def update_issue(self, issue_id: int, issue_update: IssueUpdate) -> Optional[Issue]:
        """Update issue status."""
        try:
            update_data = issue_update.dict(exclude_unset=True)
            if not update_data:
                return await self.get_issue_by_id(issue_id)
            
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            # Set resolution timestamp if resolving
            if update_data.get('is_resolved') is True:
                update_data['resolved_at'] = datetime.now(timezone.utc)
            
            await self.db.execute(
                update(Issue)
                .where(Issue.id == issue_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            updated_issue = await self.get_issue_by_id(issue_id)
            logger.info(f"Updated issue: {issue_id}")
            return updated_issue
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating issue {issue_id}: {e}")
            raise
    
    # Comment Management Methods
    
    async def create_comment(
        self,
        comment_create: CommentCreate,
        author_id: int,
        review_id: Optional[int] = None,
    ) -> Comment:
        """Create a new comment."""
        try:
            comment_data = comment_create.dict()
            comment_data['author_id'] = author_id
            
            if review_id:
                comment_data['review_id'] = review_id
            
            comment = Comment(**comment_data)
            
            self.db.add(comment)
            await self.db.commit()
            await self.db.refresh(comment)
            
            logger.info(f"Created comment by user {author_id}")
            return comment
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating comment: {e}")
            raise
    
    async def get_review_comments(self, review_id: int) -> List[Comment]:
        """Get all comments for a review."""
        try:
            result = await self.db.execute(
                select(Comment)
                .options(selectinload(Comment.author))
                .where(Comment.review_id == review_id)
                .order_by(asc(Comment.created_at))
            )
            
            comments = result.scalars().all()
            return list(comments)
            
        except Exception as e:
            logger.error(f"Error getting review comments: {e}")
            return []
    
    # Statistics and Analytics Methods
    
    async def get_review_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive review statistics for a user."""
        try:
            # Get all reviews for user's repositories
            result = await self.db.execute(
                select(Review)
                .join(Repository)
                .where(Repository.owner_id == user_id)
            )
            reviews = result.scalars().all()
            
            stats = {
                'total_reviews': len(reviews),
                'completed_reviews': 0,
                'pending_reviews': 0,
                'in_progress_reviews': 0,
                'failed_reviews': 0,
                'average_quality_score': 0.0,
                'average_security_score': 0.0,
                'total_issues_found': 0,
                'critical_issues_found': 0,
                'high_issues_found': 0,
                'issues_resolved': 0,
                'average_review_time': 0,
                'review_frequency': 0,
                'top_issue_categories': [],
                'quality_trend': 'stable',
            }
            
            if not reviews:
                return stats
            
            # Calculate basic counts
            completed_reviews = []
            for review in reviews:
                if review.status == ReviewStatus.COMPLETED:
                    completed_reviews.append(review)
                    stats['completed_reviews'] += 1
                elif review.status == ReviewStatus.PENDING:
                    stats['pending_reviews'] += 1
                elif review.status == ReviewStatus.IN_PROGRESS:
                    stats['in_progress_reviews'] += 1
                elif review.status == ReviewStatus.FAILED:
                    stats['failed_reviews'] += 1
            
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
                stats['high_issues_found'] = sum(r.high_issues for r in completed_reviews)
                
                # Calculate average review time
                review_times = []
                for review in completed_reviews:
                    if review.completed_at:
                        duration = (review.completed_at - review.created_at).total_seconds() / 60  # minutes
                        review_times.append(duration)
                
                if review_times:
                    stats['average_review_time'] = sum(review_times) / len(review_times)
                
                # Calculate quality trend
                if len(completed_reviews) >= 5:
                    recent_reviews = sorted(completed_reviews, key=lambda r: r.created_at)[-5:]
                    if all(r.code_quality_score for r in recent_reviews):
                        scores = [r.code_quality_score for r in recent_reviews]
                        first_half_avg = sum(scores[:2]) / 2
                        second_half_avg = sum(scores[-2:]) / 2
                        
                        if second_half_avg > first_half_avg + 0.5:
                            stats['quality_trend'] = 'improving'
                        elif second_half_avg < first_half_avg - 0.5:
                            stats['quality_trend'] = 'declining'
            
            # Get issue category statistics
            category_stats = await self._get_issue_category_stats(user_id)
            stats['top_issue_categories'] = category_stats
            
            # Get resolved issues count
            resolved_count = await self._get_resolved_issues_count(user_id)
            stats['issues_resolved'] = resolved_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting review statistics: {e}")
            return {}
    
    async def _get_issue_category_stats(self, user_id: int) -> List[Dict[str, Any]]:
        """Get issue statistics by category."""
        try:
            result = await self.db.execute(
                select(Issue.category, func.count(Issue.id).label('count'))
                .join(Review)
                .join(Repository)
                .where(Repository.owner_id == user_id)
                .group_by(Issue.category)
                .order_by(desc('count'))
                .limit(10)
            )
            
            category_stats = []
            for row in result:
                category_stats.append({
                    'category': row.category,
                    'count': row.count,
                })
            
            return category_stats
            
        except Exception as e:
            logger.error(f"Error getting issue category stats: {e}")
            return []
    
    async def _get_resolved_issues_count(self, user_id: int) -> int:
        """Get count of resolved issues for user."""
        try:
            result = await self.db.execute(
                select(func.count(Issue.id))
                .join(Review)
                .join(Repository)
                .where(
                    and_(
                        Repository.owner_id == user_id,
                        Issue.is_resolved == True
                    )
                )
            )
            
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting resolved issues count: {e}")
            return 0
    
    async def get_repository_by_id(self, repository_id: int) -> Optional[Repository]:
        """Get repository by ID."""
        try:
            result = await self.db.execute(
                select(Repository).where(Repository.id == repository_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting repository by ID {repository_id}: {e}")
            return None
    
    async def get_reviews_by_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Review]:
        """Get reviews within a date range."""
        try:
            result = await self.db.execute(
                select(Review)
                .join(Repository)
                .where(
                    and_(
                        Repository.owner_id == user_id,
                        Review.created_at >= start_date,
                        Review.created_at <= end_date
                    )
                )
                .order_by(desc(Review.created_at))
            )
            
            reviews = result.scalars().all()
            return list(reviews)
            
        except Exception as e:
            logger.error(f"Error getting reviews by date range: {e}")
            return []
    
    async def get_review_metrics_by_repository(self, repository_id: int) -> Dict[str, Any]:
        """Get review metrics for a specific repository."""
        try:
            result = await self.db.execute(
                select(Review).where(Review.repository_id == repository_id)
            )
            reviews = result.scalars().all()
            
            if not reviews:
                return {}
            
            completed_reviews = [r for r in reviews if r.status == ReviewStatus.COMPLETED]
            
            metrics = {
                'total_reviews': len(reviews),
                'completed_reviews': len(completed_reviews),
                'completion_rate': len(completed_reviews) / len(reviews) * 100,
                'average_quality_score': 0.0,
                'total_issues': sum(r.total_issues for r in completed_reviews),
                'critical_issues': sum(r.critical_issues for r in completed_reviews),
                'issues_per_review': 0.0,
                'last_review_date': None,
            }
            
            if completed_reviews:
                quality_scores = [r.code_quality_score for r in completed_reviews if r.code_quality_score]
                if quality_scores:
                    metrics['average_quality_score'] = sum(quality_scores) / len(quality_scores)
                
                metrics['issues_per_review'] = metrics['total_issues'] / len(completed_reviews)
                
                latest_review = max(completed_reviews, key=lambda r: r.created_at)
                metrics['last_review_date'] = latest_review.created_at.isoformat()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting repository review metrics: {e}")
            return {}


# Review Analytics Service
class ReviewAnalyticsService:
    """Advanced analytics and reporting for code reviews."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.review_service = ReviewService(db)
    
    async def generate_team_report(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Generate comprehensive team review report."""
        try:
            reviews = await self.review_service.get_reviews_by_date_range(
                user_id, start_date, end_date
            )
            
            if not reviews:
                return {'message': 'No reviews found for the specified period'}
            
            # Calculate report metrics
            completed_reviews = [r for r in reviews if r.status == ReviewStatus.COMPLETED]
            
            report = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days,
                },
                'summary': {
                    'total_reviews': len(reviews),
                    'completed_reviews': len(completed_reviews),
                    'completion_rate': len(completed_reviews) / len(reviews) * 100 if reviews else 0,
                    'average_quality_score': 0.0,
                    'total_issues_found': sum(r.total_issues for r in completed_reviews),
                    'critical_issues_found': sum(r.critical_issues for r in completed_reviews),
                },
                'trends': await self._analyze_quality_trends(completed_reviews),
                'issue_analysis': await self._analyze_issue_patterns(user_id, start_date, end_date),
                'recommendations': await self._generate_improvement_recommendations(completed_reviews),
            }
            
            # Calculate average quality score
            if completed_reviews:
                quality_scores = [r.code_quality_score for r in completed_reviews if r.code_quality_score]
                if quality_scores:
                    report['summary']['average_quality_score'] = sum(quality_scores) / len(quality_scores)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating team report: {e}")
            return {}
    
    async def _analyze_quality_trends(self, reviews: List[Review]) -> Dict[str, Any]:
        """Analyze quality trends over time."""
        try:
            if len(reviews) < 2:
                return {'trend': 'insufficient_data'}
            
            # Sort by date and group by week
            sorted_reviews = sorted(reviews, key=lambda r: r.created_at)
            
            weekly_scores = {}
            for review in sorted_reviews:
                if review.code_quality_score:
                    week_key = review.created_at.strftime('%Y-W%U')
                    if week_key not in weekly_scores:
                        weekly_scores[week_key] = []
                    weekly_scores[week_key].append(review.code_quality_score)
            
            # Calculate weekly averages
            weekly_averages = {}
            for week, scores in weekly_scores.items():
                weekly_averages[week] = sum(scores) / len(scores)
            
            # Determine trend
            if len(weekly_averages) >= 2:
                weeks = sorted(weekly_averages.keys())
                first_half = weeks[:len(weeks)//2]
                second_half = weeks[len(weeks)//2:]
                
                first_avg = sum(weekly_averages[w] for w in first_half) / len(first_half)
                second_avg = sum(weekly_averages[w] for w in second_half) / len(second_half)
                
                if second_avg > first_avg + 0.5:
                    trend = 'improving'
                elif second_avg < first_avg - 0.5:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            return {
                'trend': trend,
                'weekly_averages': weekly_averages,
                'data_points': len(sorted_reviews),
            }
            
        except Exception as e:
            logger.error(f"Error analyzing quality trends: {e}")
            return {'trend': 'error'}
    
    async def _analyze_issue_patterns(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Analyze common issue patterns."""
        try:
            result = await self.db.execute(
                select(Issue)
                .join(Review)
                .join(Repository)
                .where(
                    and_(
                        Repository.owner_id == user_id,
                        Review.created_at >= start_date,
                        Review.created_at <= end_date
                    )
                )
            )
            
            issues = result.scalars().all()
            
            if not issues:
                return {'message': 'No issues found'}
            
            # Analyze patterns
            category_counts = {}
            severity_counts = {}
            file_patterns = {}
            
            for issue in issues:
                # Category analysis
                category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
                
                # Severity analysis
                severity_counts[issue.severity.value] = severity_counts.get(issue.severity.value, 0) + 1
                
                # File pattern analysis
                file_ext = issue.file_path.split('.')[-1] if '.' in issue.file_path else 'unknown'
                file_patterns[file_ext] = file_patterns.get(file_ext, 0) + 1
            
            return {
                'total_issues': len(issues),
                'category_breakdown': category_counts,
                'severity_breakdown': severity_counts,
                'file_type_breakdown': file_patterns,
                'most_common_category': max(category_counts, key=category_counts.get) if category_counts else None,
                'resolution_rate': sum(1 for i in issues if i.is_resolved) / len(issues) * 100,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing issue patterns: {e}")
            return {}
    
    async def _generate_improvement_recommendations(self, reviews: List[Review]) -> List[Dict[str, Any]]:
        """Generate improvement recommendations based on review data."""
        recommendations = []
        
        try:
            if not reviews:
                return recommendations
            
            # Calculate averages
            avg_quality_score = 0
            avg_security_score = 0
            total_critical_issues = 0
            total_issues = 0
            
            quality_scores = [r.code_quality_score for r in reviews if r.code_quality_score]
            security_scores = [r.security_score for r in reviews if r.security_score]
            
            if quality_scores:
                avg_quality_score = sum(quality_scores) / len(quality_scores)
            
            if security_scores:
                avg_security_score = sum(security_scores) / len(security_scores)
            
            total_critical_issues = sum(r.critical_issues for r in reviews)
            total_issues = sum(r.total_issues for r in reviews)
            
            # Generate recommendations based on metrics
            if avg_quality_score < 7.0:
                recommendations.append({
                    'category': 'code_quality',
                    'priority': 'high',
                    'title': 'Improve Code Quality Standards',
                    'description': f'Average quality score is {avg_quality_score:.1f}/10. Consider implementing stricter code review guidelines.',
                    'actions': [
                        'Establish coding standards documentation',
                        'Implement automated linting and formatting',
                        'Provide code quality training for team members',
                        'Set quality gates in CI/CD pipeline',
                    ]
                })
            
            if avg_security_score < 8.0:
                recommendations.append({
                    'category': 'security',
                    'priority': 'high',
                    'title': 'Enhance Security Practices',
                    'description': f'Average security score is {avg_security_score:.1f}/10. Security practices need improvement.',
                    'actions': [
                        'Conduct security training sessions',
                        'Implement security-focused code review checklist',
                        'Add automated security scanning tools',
                        'Regular security audits of codebase',
                    ]
                })
            
            if total_critical_issues > len(reviews) * 2:  # More than 2 critical issues per review on average
                recommendations.append({
                    'category': 'critical_issues',
                    'priority': 'high',
                    'title': 'Reduce Critical Issues',
                    'description': f'Found {total_critical_issues} critical issues across {len(reviews)} reviews.',
                    'actions': [
                        'Implement pre-commit hooks for critical issue detection',
                        'Enhance unit testing coverage',
                        'Add integration testing for critical paths',
                        'Create issue prevention guidelines',
                    ]
                })
            
            # Performance recommendation
            completion_rate = len([r for r in reviews if r.status == ReviewStatus.COMPLETED]) / len(reviews)
            if completion_rate < 0.8:
                recommendations.append({
                    'category': 'process',
                    'priority': 'medium',
                    'title': 'Improve Review Completion Rate',
                    'description': f'Only {completion_rate*100:.1f}% of reviews are completed.',
                    'actions': [
                        'Set clear review deadlines',
                        'Implement review assignment system',
                        'Add review progress monitoring',
                        'Provide reviewer training and support',
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

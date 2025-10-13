import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.models.database.user import User
from app.models.schemas.user import UserCreate, UserUpdate, UserInDB
from app.core.security import get_password_hash, verify_password
from app.core.config import settings

logger = logging.getLogger(__name__)

class UserService:
    """Comprehensive user management service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user with comprehensive validation."""
        try:
            # Check if user already exists
            existing_user = await self.get_by_email(user_create.email)
            if existing_user:
                raise ValueError(f"User with email {user_create.email} already exists")
            
            existing_user = await self.get_by_username(user_create.username)
            if existing_user:
                raise ValueError(f"User with username {user_create.username} already exists")
            
            # Hash the password
            hashed_password = get_password_hash(user_create.password)
            
            # Create user object
            user_data = {
                'email': user_create.email.lower(),
                'username': user_create.username,
                'full_name': user_create.full_name,
                'avatar_url': user_create.avatar_url,
                'bio': user_create.bio,
                'location': user_create.location,
                'company': user_create.company,
                'website': user_create.website,
                'hashed_password': hashed_password,
                'is_active': True,
                'is_verified': False,
                'preferences': self._get_default_preferences(),
                'notification_settings': self._get_default_notification_settings(),
            }
            
            user = User(**user_data)
            
            # Add to database
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Created new user: {user.email} (ID: {user.id})")
            return user
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Database integrity error creating user: {e}")
            raise ValueError("User with this email or username already exists")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        try:
            # Handle None email (for OAuth users with private emails)
            if email is None:
                return None
            
            result = await self.db.execute(
                select(User).where(User.email == email.lower())
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            result = await self.db.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    async def get_by_oauth_id(self, provider: str, oauth_id: str) -> Optional[User]:
        """Get user by OAuth provider ID."""
        try:
            if provider == 'github':
                result = await self.db.execute(
                    select(User).where(User.github_id == oauth_id)
                )
            elif provider == 'gitlab':
                result = await self.db.execute(
                    select(User).where(User.gitlab_id == oauth_id)
                )
            elif provider == 'bitbucket':
                result = await self.db.execute(
                    select(User).where(User.bitbucket_id == oauth_id)
                )
            else:
                return None
                
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by OAuth ID {oauth_id}: {e}")
            return None
    
    async def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update user information."""
        try:
            # Get existing user
            user = await self.get_by_id(user_id)
            if not user:
                return None
            
            # Prepare update data
            update_data = {}
            
            for field, value in user_update.dict(exclude_unset=True).items():
                if value is not None:
                    if field == 'email':
                        # Check if new email is already taken
                        existing_user = await self.get_by_email(value)
                        if existing_user and existing_user.id != user_id:
                            raise ValueError(f"Email {value} is already taken")
                        update_data[field] = value.lower()
                    elif field == 'username':
                        # Check if new username is already taken
                        existing_user = await self.get_by_username(value)
                        if existing_user and existing_user.id != user_id:
                            raise ValueError(f"Username {value} is already taken")
                        update_data[field] = value
                    else:
                        update_data[field] = value
            
            if update_data:
                update_data['updated_at'] = datetime.now(timezone.utc)
                
                # Update user
                await self.db.execute(
                    update(User).where(User.id == user_id).values(**update_data)
                )
                await self.db.commit()
                
                # Refresh user data
                updated_user = await self.get_by_id(user_id)
                logger.info(f"Updated user: {updated_user.email} (ID: {user_id})")
                return updated_user
            
            return user
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    async def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password."""
        try:
            hashed_password = get_password_hash(new_password)
            
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    hashed_password=hashed_password,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.commit()
            
            logger.info(f"Updated password for user ID: {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating password for user {user_id}: {e}")
            return False
    
    async def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        try:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(last_login=datetime.now(timezone.utc))
            )
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating last login for user {user_id}: {e}")
            return False
    
    async def authenticate_user(self, email_or_username: str, password: str) -> Optional[User]:
        """Authenticate user with email/username and password."""
        try:
            # Try to find user by email first, then by username
            user = await self.get_by_email(email_or_username)
            if not user:
                user = await self.get_by_username(email_or_username)
            
            if not user:
                logger.warning(f"Authentication failed: user not found for {email_or_username}")
                return None
            
            if not user.is_active:
                logger.warning(f"Authentication failed: inactive user {email_or_username}")
                return None
            
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password for {email_or_username}")
                return None
            
            # Update last login
            await self.update_last_login(user.id)
            
            logger.info(f"Successful authentication for user: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user {email_or_username}: {e}")
            return None
    
    async def create_or_update_oauth_user(
        self,
        provider: str,
        oauth_id: str,
        email: str,
        username: str,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        github_access_token: Optional[str] = None,  # NEW PARAMETER
    ) -> User:
        """Create or update user from OAuth provider."""
        try:
            # Check if user exists by OAuth ID
            user = await self.get_by_oauth_id(provider, oauth_id)
            
            if user:
                # Update existing OAuth user
                update_data = {
                    'full_name': full_name or user.full_name,
                    'avatar_url': avatar_url or user.avatar_url,
                    'updated_at': datetime.now(timezone.utc),
                    'last_login': datetime.now(timezone.utc),
                }
                
                # Only update email if it's provided and not None
                if email is not None:
                    update_data['email'] = email.lower()
                
                # Store GitHub access token if provided
                if github_access_token and provider == "github":
                    # Get current preferences and add the token
                    current_prefs = user.preferences or {}
                    current_prefs['github_access_token'] = github_access_token
                    update_data['preferences'] = current_prefs
                
                await self.db.execute(
                    update(User).where(User.id == user.id).values(**update_data)
                )
                await self.db.commit()
                
                updated_user = await self.get_by_id(user.id)
                logger.info(f"Updated OAuth user: {updated_user.email} (Provider: {provider})")
                return updated_user
            
            # Check if user exists by email (only if email is provided)
            if email is not None:
                user = await self.get_by_email(email)
                if user:
                    # Link OAuth account to existing user
                    oauth_field = f"{provider}_id"
                    link_data = {
                        oauth_field: oauth_id,
                        'avatar_url': avatar_url or user.avatar_url,
                        'updated_at': datetime.now(timezone.utc),
                        'last_login': datetime.now(timezone.utc),
                    }
                    
                    # Store GitHub access token if provided
                    if github_access_token and provider == "github":
                        current_prefs = user.preferences or {}
                        current_prefs['github_access_token'] = github_access_token
                        link_data['preferences'] = current_prefs
                    
                    await self.db.execute(
                        update(User)
                        .where(User.id == user.id)
                        .values(**link_data)
                    )
                    await self.db.commit()
                    
                    updated_user = await self.get_by_id(user.id)
                    logger.info(f"Linked {provider} account to existing user: {updated_user.email}")
                    return updated_user
            
            # Create new OAuth user
            # Generate email if not provided (for private GitHub emails)
            if email is None:
                email = f"{provider}_{oauth_id}@oauth.local"
            
            # Get default preferences
            preferences = self._get_default_preferences()
            
            # Store GitHub access token if provided
            if github_access_token and provider == "github":
                preferences['github_access_token'] = github_access_token
            
            user_data = {
                'email': email.lower(),
                'username': await self._generate_unique_username(username),
                'full_name': full_name,
                'avatar_url': avatar_url,
                'hashed_password': get_password_hash(f"oauth_{oauth_id}_{provider}"),  # Dummy password
                'is_active': True,
                'is_verified': True,  # OAuth users are pre-verified
                'preferences': preferences,  # Updated preferences with token
                'notification_settings': self._get_default_notification_settings(),
                'last_login': datetime.now(timezone.utc),
            }
            
            # Set OAuth provider ID
            oauth_field = f"{provider}_id"
            user_data[oauth_field] = oauth_id
            
            user = User(**user_data)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Created new OAuth user: {user.email} (Provider: {provider})")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating/updating OAuth user: {e}")
            raise
    
    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account."""
        try:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    is_active=False,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.commit()
            
            logger.info(f"Deactivated user ID: {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deactivating user {user_id}: {e}")
            return False
    
    async def activate_user(self, user_id: int) -> bool:
        """Activate user account."""
        try:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    is_active=True,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.commit()
            
            logger.info(f"Activated user ID: {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error activating user {user_id}: {e}")
            return False
    
    async def verify_user(self, user_id: int) -> bool:
        """Mark user as verified."""
        try:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    is_verified=True,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.commit()
            
            logger.info(f"Verified user ID: {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error verifying user {user_id}: {e}")
            return False
    
    async def delete_user(self, user_id: int) -> bool:
        """Permanently delete user account and associated data."""
        try:
            # This would typically involve deleting associated data first
            # In production, consider soft delete or data retention policies
            
            await self.db.execute(
                delete(User).where(User.id == user_id)
            )
            await self.db.commit()
            
            logger.info(f"Deleted user ID: {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def get_user_list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[User]:
        """Get paginated list of users with filtering."""
        try:
            query = select(User)
            
            # Apply filters
            filters = []
            
            if search:
                search_pattern = f"%{search.lower()}%"
                filters.append(
                    or_(
                        User.email.ilike(search_pattern),
                        User.username.ilike(search_pattern),
                        User.full_name.ilike(search_pattern)
                    )
                )
            
            if is_active is not None:
                filters.append(User.is_active == is_active)
            
            if is_verified is not None:
                filters.append(User.is_verified == is_verified)
            
            if filters:
                query = query.where(and_(*filters))
            
            # Apply ordering
            if hasattr(User, order_by):
                order_column = getattr(User, order_by)
                if order_desc:
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            users = result.scalars().all()
            
            return list(users)
            
        except Exception as e:
            logger.error(f"Error getting user list: {e}")
            return []
    
    async def get_user_count(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
    ) -> int:
        """Get total count of users matching filters."""
        try:
            query = select(func.count(User.id))
            
            # Apply filters
            filters = []
            
            if search:
                search_pattern = f"%{search.lower()}%"
                filters.append(
                    or_(
                        User.email.ilike(search_pattern),
                        User.username.ilike(search_pattern),
                        User.full_name.ilike(search_pattern)
                    )
                )
            
            if is_active is not None:
                filters.append(User.is_active == is_active)
            
            if is_verified is not None:
                filters.append(User.is_verified == is_verified)
            
            if filters:
                query = query.where(and_(*filters))
            
            result = await self.db.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            return 0
    
    async def update_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user preferences."""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # Merge with existing preferences
            current_prefs = user.preferences or {}
            updated_prefs = {**current_prefs, **preferences}
            
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    preferences=updated_prefs,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.commit()
            
            logger.info(f"Updated preferences for user ID: {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            return False
    
    async def update_notification_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Update user notification settings."""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # Merge with existing settings
            current_settings = user.notification_settings or {}
            updated_settings = {**current_settings, **settings}
            
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    notification_settings=updated_settings,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await self.db.commit()
            
            logger.info(f"Updated notification settings for user ID: {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating notification settings for user {user_id}: {e}")
            return False
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        try:
            # Total users
            total_users_result = await self.db.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar() or 0
            
            # Active users
            active_users_result = await self.db.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            active_users = active_users_result.scalar() or 0
            
            # Verified users
            verified_users_result = await self.db.execute(
                select(func.count(User.id)).where(User.is_verified == True)
            )
            verified_users = verified_users_result.scalar() or 0
            
            # OAuth users
            github_users_result = await self.db.execute(
                select(func.count(User.id)).where(User.github_id.isnot(None))
            )
            github_users = github_users_result.scalar() or 0
            
            gitlab_users_result = await self.db.execute(
                select(func.count(User.id)).where(User.gitlab_id.isnot(None))
            )
            gitlab_users = gitlab_users_result.scalar() or 0
            
            # Recent registrations (last 30 days)
            thirty_days_ago = datetime.now(timezone.utc).replace(day=1)  # Simplified for example
            recent_registrations_result = await self.db.execute(
                select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
            )
            recent_registrations = recent_registrations_result.scalar() or 0
            
            statistics = {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users,
                'github_users': github_users,
                'gitlab_users': gitlab_users,
                'recent_registrations': recent_registrations,
                'activation_rate': (active_users / total_users * 100) if total_users > 0 else 0,
                'verification_rate': (verified_users / total_users * 100) if total_users > 0 else 0,
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}
    
    async def _generate_unique_username(self, base_username: str) -> str:
        """Generate a unique username by appending numbers if necessary."""
        try:
            username = base_username
            counter = 1
            
            while True:
                existing_user = await self.get_by_username(username)
                if not existing_user:
                    return username
                
                username = f"{base_username}{counter}"
                counter += 1
                
                # Prevent infinite loop
                if counter > 9999:
                    import uuid
                    return f"{base_username}_{uuid.uuid4().hex[:8]}"
                    
        except Exception as e:
            logger.error(f"Error generating unique username: {e}")
            import uuid
            return f"{base_username}_{uuid.uuid4().hex[:8]}"
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default user preferences."""
        return {
            'theme': 'light',
            'language': 'en',
            'timezone': 'UTC',
            'email_notifications': True,
            'push_notifications': True,
            'auto_review': True,
            'review_complexity_threshold': 'medium',
            'code_style_checks': True,
            'security_checks': True,
            'performance_checks': True,
        }
    
    def _get_default_notification_settings(self) -> Dict[str, Any]:
        """Get default notification settings."""
        return {
            'email_on_review_complete': True,
            'email_on_critical_issues': True,
            'email_on_security_issues': True,
            'email_weekly_summary': True,
            'push_on_review_complete': False,
            'push_on_critical_issues': True,
            'slack_notifications': False,
            'slack_webhook_url': None,
        }

# User Profile Management Service
class UserProfileService:
    """Service for managing user profiles and social features."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
    
    async def get_public_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get public user profile information."""
        try:
            user = await self.user_service.get_by_id(user_id)
            if not user:
                return None
            
            # Load user with repositories and reviews for statistics
            result = await self.db.execute(
                select(User)
                .options(
                    selectinload(User.repositories),
                    selectinload(User.reviews)
                )
                .where(User.id == user_id)
            )
            user_with_stats = result.scalar_one_or_none()
            
            if not user_with_stats:
                return None
            
            # Calculate profile statistics
            stats = await self._calculate_profile_stats(user_with_stats)
            
            public_profile = {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'avatar_url': user.avatar_url,
                'bio': user.bio,
                'location': user.location,
                'company': user.company,
                'website': user.website,
                'created_at': user.created_at.isoformat(),
                'stats': stats,
                'is_verified': user.is_verified,
            }
            
            return public_profile
            
        except Exception as e:
            logger.error(f"Error getting public profile for user {user_id}: {e}")
            return None
    
    async def _calculate_profile_stats(self, user: User) -> Dict[str, Any]:
        """Calculate user profile statistics."""
        try:
            stats = {
                'total_repositories': len(user.repositories) if user.repositories else 0,
                'total_reviews': len(user.reviews) if user.reviews else 0,
                'active_repositories': 0,
                'completed_reviews': 0,
                'average_quality_score': 0.0,
                'total_issues_found': 0,
                'languages': [],
                'join_date': user.created_at.isoformat(),
            }
            
            # Calculate repository statistics
            if user.repositories:
                active_repos = [r for r in user.repositories if r.is_active and not r.is_archived]
                stats['active_repositories'] = len(active_repos)
                
                # Get language distribution
                language_count = {}
                for repo in user.repositories:
                    if repo.language:
                        language_count[repo.language] = language_count.get(repo.language, 0) + 1
                
                stats['languages'] = [
                    {'name': lang, 'count': count}
                    for lang, count in sorted(language_count.items(), key=lambda x: x[1], reverse=True)
                ]
            
            # Calculate review statistics
            if user.reviews:
                completed_reviews = [r for r in user.reviews if r.status == 'completed']
                stats['completed_reviews'] = len(completed_reviews)
                
                if completed_reviews:
                    # Calculate average quality score
                    quality_scores = [r.code_quality_score for r in completed_reviews if r.code_quality_score]
                    if quality_scores:
                        stats['average_quality_score'] = sum(quality_scores) / len(quality_scores)
                    
                    # Calculate total issues found
                    stats['total_issues_found'] = sum(r.total_issues for r in completed_reviews)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating profile stats: {e}")
            return {}

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import re
from urllib.parse import urlparse

from app.core.config import settings
from app.models.database.user import User

logger = logging.getLogger(__name__)

class IntegrationService:
    """Service for integrating with external VCS providers."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def validate_repository_access(
        self,
        provider: str,
        repository_url: str,
        access_token: Optional[str] = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Validate repository access and return repository information."""
        if provider == "github":
            return await self._validate_github_repo(repository_url, access_token)
        elif provider == "gitlab":
            return await self._validate_gitlab_repo(repository_url, access_token)
        elif provider == "bitbucket":
            return await self._validate_bitbucket_repo(repository_url, access_token)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def setup_webhook(
        self,
        provider: str,
        repository_id: str,
        webhook_url: str,
        access_token: str
    ) -> Optional[str]:
        """Setup webhook for repository."""
        if provider == "github":
            return await self._setup_github_webhook(repository_id, webhook_url, access_token)
        elif provider == "gitlab":
            return await self._setup_gitlab_webhook(repository_id, webhook_url, access_token)
        elif provider == "bitbucket":
            return await self._setup_bitbucket_webhook(repository_id, webhook_url, access_token)
        else:
            logger.warning(f"Webhook setup not supported for provider: {provider}")
            return None
    
    async def remove_webhook(
        self,
        provider: str,
        webhook_id: str,
        access_token: Optional[str] = None
    ) -> bool:
        """Remove webhook from repository."""
        if provider == "github":
            return await self._remove_github_webhook(webhook_id, access_token)
        elif provider == "gitlab":
            return await self._remove_gitlab_webhook(webhook_id, access_token)
        elif provider == "bitbucket":
            return await self._remove_bitbucket_webhook(webhook_id, access_token)
        else:
            logger.warning(f"Webhook removal not supported for provider: {provider}")
            return False
    
    async def get_repository_branches(
        self,
        provider: str,
        repository_id: str,
        access_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get repository branches."""
        if provider == "github":
            return await self._get_github_branches(repository_id, access_token)
        elif provider == "gitlab":
            return await self._get_gitlab_branches(repository_id, access_token)
        elif provider == "bitbucket":
            return await self._get_bitbucket_branches(repository_id, access_token)
        else:
            logger.warning(f"Branch fetching not supported for provider: {provider}")
            return []
    
    # GitHub Integration Methods
    async def _validate_github_repo(self, repository_url: str, access_token: Optional[str]) -> Dict[str, Any]:
        """Validate GitHub repository access."""
        # Extract owner and repo from URL
        pattern = r"https://github\.com/([^/]+)/([^/]+)/?.*"
        match = re.match(pattern, repository_url)
        
        if not match:
            raise ValueError("Invalid GitHub repository URL")
        
        owner, repo = match.groups()
        repo = repo.replace('.git', '')  # Remove .git if present
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        if access_token:
            headers["Authorization"] = f"token {access_token}"
        
        url = f"https://api.github.com/repos/{owner}/{repo}"
        
        try:
            response = await self.session.get(url, headers=headers)
            
            if response.status_code == 404:
                raise ValueError("Repository not found or access denied")
            elif response.status_code == 403:
                raise ValueError("Rate limit exceeded or insufficient permissions")
            elif response.status_code != 200:
                raise ValueError(f"GitHub API error: {response.status_code} - {response.text}")
            
            repo_data = response.json()
            
            return {
                "id": repo_data["id"],
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "description": repo_data.get("description"),
                "url": repo_data["html_url"],
                "clone_url": repo_data["clone_url"],
                "default_branch": repo_data["default_branch"],
                "language": repo_data.get("language"),
                "is_private": repo_data["private"],
                "size": repo_data.get("size", 0),
                "owner": repo_data["owner"]["login"],
                "created_at": repo_data["created_at"],
                "updated_at": repo_data["updated_at"],
            }
            
        except httpx.RequestError as e:
            logger.error(f"Network error during GitHub API request: {e}")
            raise ValueError("Network error connecting to GitHub")
        except Exception as e:
            logger.error(f"GitHub validation error: {e}")
            raise
    
    async def _setup_github_webhook(self, repository_full_name: str, webhook_url: str, access_token: str) -> Optional[str]:
        """Setup GitHub webhook."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {access_token}",
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        webhook_data = {
            "name": "web",
            "active": True,
            "events": ["push", "pull_request", "pull_request_review"],
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        url = f"https://api.github.com/repos/{repository_full_name}/hooks"
        
        try:
            response = await self.session.post(url, headers=headers, json=webhook_data)
            
            if response.status_code == 201:
                webhook_response = response.json()
                return str(webhook_response["id"])
            else:
                logger.error(f"GitHub webhook setup failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"GitHub webhook setup error: {e}")
            return None
    
    async def _remove_github_webhook(self, repository_full_name: str, webhook_id: str, access_token: str) -> bool:
        """Remove GitHub webhook."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {access_token}",
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        url = f"https://api.github.com/repos/{repository_full_name}/hooks/{webhook_id}"
        
        try:
            response = await self.session.delete(url, headers=headers)
            return response.status_code == 204
        except Exception as e:
            logger.error(f"GitHub webhook removal error: {e}")
            return False
    
    async def _get_github_branches(self, repository_full_name: str, access_token: Optional[str]) -> List[Dict[str, Any]]:
        """Get GitHub repository branches."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        if access_token:
            headers["Authorization"] = f"token {access_token}"
        
        url = f"https://api.github.com/repos/{repository_full_name}/branches"
        
        try:
            response = await self.session.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"GitHub branches API error: {response.status_code}")
                return []
            
            branches_data = response.json()
            branches = []
            
            for branch in branches_data:
                branches.append({
                    "name": branch["name"],
                    "protected": branch.get("protected", False),
                    "default": False,  # Will be set later
                    "commit_sha": branch["commit"]["sha"],
                    "commit_url": branch["commit"]["url"]
                })
            
            return branches
            
        except Exception as e:
            logger.error(f"GitHub branches error: {e}")
            return []
    
    # GitLab Integration Methods
    async def _validate_gitlab_repo(self, repository_url: str, access_token: Optional[str]) -> Dict[str, Any]:
        """Validate GitLab repository access."""
        # Parse GitLab URL
        parsed_url = urlparse(repository_url)
        if 'gitlab.com' not in parsed_url.netloc and 'gitlab' not in parsed_url.netloc:
            raise ValueError("Invalid GitLab repository URL")
        
        # Extract project path
        path = parsed_url.path.strip('/').replace('.git', '')
        project_path = path.replace('/', '%2F')  # URL encode the slash
        
        headers = {
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        # Default to gitlab.com if no host specified
        gitlab_host = parsed_url.netloc if parsed_url.netloc else "gitlab.com"
        url = f"https://{gitlab_host}/api/v4/projects/{project_path}"
        
        try:
            response = await self.session.get(url, headers=headers)
            
            if response.status_code == 404:
                raise ValueError("Repository not found or access denied")
            elif response.status_code != 200:
                raise ValueError(f"GitLab API error: {response.status_code} - {response.text}")
            
            repo_data = response.json()
            
            return {
                "id": str(repo_data["id"]),
                "name": repo_data["name"],
                "full_name": repo_data["path_with_namespace"],
                "description": repo_data.get("description"),
                "url": repo_data["web_url"],
                "clone_url": repo_data["http_url_to_repo"],
                "default_branch": repo_data["default_branch"],
                "language": None,  # GitLab doesn't provide primary language in project API
                "is_private": repo_data["visibility"] == "private",
                "size": 0,  # GitLab doesn't provide repository size
                "created_at": repo_data["created_at"],
                "updated_at": repo_data["last_activity_at"],
            }
            
        except httpx.RequestError as e:
            logger.error(f"Network error during GitLab API request: {e}")
            raise ValueError("Network error connecting to GitLab")
        except Exception as e:
            logger.error(f"GitLab validation error: {e}")
            raise
    
    async def _setup_gitlab_webhook(self, project_id: str, webhook_url: str, access_token: str) -> Optional[str]:
        """Setup GitLab webhook."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        webhook_data = {
            "url": webhook_url,
            "push_events": True,
            "merge_requests_events": True,
            "enable_ssl_verification": True
        }
        
        url = f"https://gitlab.com/api/v4/projects/{project_id}/hooks"
        
        try:
            response = await self.session.post(url, headers=headers, json=webhook_data)
            
            if response.status_code == 201:
                webhook_response = response.json()
                return str(webhook_response["id"])
            else:
                logger.error(f"GitLab webhook setup failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"GitLab webhook setup error: {e}")
            return None
    
    async def _remove_gitlab_webhook(self, project_id: str, webhook_id: str, access_token: str) -> bool:
        """Remove GitLab webhook."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        url = f"https://gitlab.com/api/v4/projects/{project_id}/hooks/{webhook_id}"
        
        try:
            response = await self.session.delete(url, headers=headers)
            return response.status_code == 204
        except Exception as e:
            logger.error(f"GitLab webhook removal error: {e}")
            return False
    
    async def _get_gitlab_branches(self, project_id: str, access_token: Optional[str]) -> List[Dict[str, Any]]:
        """Get GitLab repository branches."""
        headers = {
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/branches"
        
        try:
            response = await self.session.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"GitLab branches API error: {response.status_code}")
                return []
            
            branches_data = response.json()
            branches = []
            
            for branch in branches_data:
                branches.append({
                    "name": branch["name"],
                    "protected": branch.get("protected", False),
                    "default": branch.get("default", False),
                    "commit_sha": branch["commit"]["id"],
                    "commit_url": branch["commit"]["web_url"]
                })
            
            return branches
            
        except Exception as e:
            logger.error(f"GitLab branches error: {e}")
            return []
    
    # Bitbucket Integration Methods
    async def _validate_bitbucket_repo(self, repository_url: str, access_token: Optional[str]) -> Dict[str, Any]:
        """Validate Bitbucket repository access."""
        # Extract workspace and repo from URL
        pattern = r"https://bitbucket\.org/([^/]+)/([^/]+)/?.*"
        match = re.match(pattern, repository_url)
        
        if not match:
            raise ValueError("Invalid Bitbucket repository URL")
        
        workspace, repo = match.groups()
        repo = repo.replace('.git', '')
        
        headers = {
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}"
        
        try:
            response = await self.session.get(url, headers=headers)
            
            if response.status_code == 404:
                raise ValueError("Repository not found or access denied")
            elif response.status_code != 200:
                raise ValueError(f"Bitbucket API error: {response.status_code} - {response.text}")
            
            repo_data = response.json()
            
            return {
                "id": repo_data["uuid"].strip('{}'),
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "description": repo_data.get("description"),
                "url": repo_data["links"]["html"]["href"],
                "clone_url": repo_data["links"]["clone"][0]["href"],
                "default_branch": repo_data.get("mainbranch", {}).get("name", "main"),
                "language": repo_data.get("language"),
                "is_private": repo_data["is_private"],
                "size": repo_data.get("size", 0),
                "created_at": repo_data["created_on"],
                "updated_at": repo_data["updated_on"],
            }
            
        except httpx.RequestError as e:
            logger.error(f"Network error during Bitbucket API request: {e}")
            raise ValueError("Network error connecting to Bitbucket")
        except Exception as e:
            logger.error(f"Bitbucket validation error: {e}")
            raise
    
    async def _setup_bitbucket_webhook(self, repository_full_name: str, webhook_url: str, access_token: str) -> Optional[str]:
        """Setup Bitbucket webhook."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "AI-Code-Review-Assistant",
            "Content-Type": "application/json"
        }
        
        webhook_data = {
            "description": "AI Code Review Assistant Webhook",
            "url": webhook_url,
            "active": True,
            "events": ["repo:push", "pullrequest:created", "pullrequest:updated"]
        }
        
        url = f"https://api.bitbucket.org/2.0/repositories/{repository_full_name}/hooks"
        
        try:
            response = await self.session.post(url, headers=headers, json=webhook_data)
            
            if response.status_code == 201:
                webhook_response = response.json()
                return webhook_response["uuid"].strip('{}')
            else:
                logger.error(f"Bitbucket webhook setup failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Bitbucket webhook setup error: {e}")
            return None
    
    async def _remove_bitbucket_webhook(self, repository_full_name: str, webhook_id: str, access_token: str) -> bool:
        """Remove Bitbucket webhook."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        url = f"https://api.bitbucket.org/2.0/repositories/{repository_full_name}/hooks/{webhook_id}"
        
        try:
            response = await self.session.delete(url, headers=headers)
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Bitbucket webhook removal error: {e}")
            return False
    
    async def _get_bitbucket_branches(self, repository_full_name: str, access_token: Optional[str]) -> List[Dict[str, Any]]:
        """Get Bitbucket repository branches."""
        headers = {
            "User-Agent": "AI-Code-Review-Assistant"
        }
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        url = f"https://api.bitbucket.org/2.0/repositories/{repository_full_name}/refs/branches"
        
        try:
            response = await self.session.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Bitbucket branches API error: {response.status_code}")
                return []
            
            data = response.json()
            branches = []
            
            for branch in data.get("values", []):
                branches.append({
                    "name": branch["name"],
                    "protected": False,  # Bitbucket doesn't provide this in branches API
                    "default": branch.get("default", False),
                    "commit_sha": branch["target"]["hash"],
                    "commit_url": branch["target"]["links"]["html"]["href"]
                })
            
            return branches
            
        except Exception as e:
            logger.error(f"Bitbucket branches error: {e}")
            return []
    
    async def close(self):
        """Clean up resources."""
        await self.session.aclose()

# OAuth Service for real authentication flows
class OAuthService:
    """Service for handling OAuth authentication with VCS providers."""
    
    @staticmethod
    async def get_github_access_token(code: str) -> Optional[str]:
        """Exchange GitHub OAuth code for access token."""
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
            logger.error("GitHub OAuth credentials not configured")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": settings.GITHUB_CLIENT_ID,
                        "client_secret": settings.GITHUB_CLIENT_SECRET,
                        "code": code,
                    },
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")
                else:
                    logger.error(f"GitHub OAuth token exchange failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"GitHub OAuth error: {e}")
            return None
    
    @staticmethod
    async def get_gitlab_access_token(code: str, redirect_uri: str) -> Optional[str]:
        """Exchange GitLab OAuth code for access token."""
        if not settings.GITLAB_CLIENT_ID or not settings.GITLAB_CLIENT_SECRET:
            logger.error("GitLab OAuth credentials not configured")
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://gitlab.com/oauth/token",
                    data={
                        "client_id": settings.GITLAB_CLIENT_ID,
                        "client_secret": settings.GITLAB_CLIENT_SECRET,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri,
                    },
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")
                else:
                    logger.error(f"GitLab OAuth token exchange failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"GitLab OAuth error: {e}")
            return None
    
    @staticmethod
    async def get_user_info(provider: str, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from provider."""
        try:
            if provider == "github":
                return await OAuthService._get_github_user_info(access_token)
            elif provider == "gitlab":
                return await OAuthService._get_gitlab_user_info(access_token)
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting user info from {provider}: {e}")
            return None
    
    @staticmethod
    async def _get_github_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """Get GitHub user information."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"GitHub user info request failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"GitHub user info error: {e}")
            return None
    
    @staticmethod
    async def _get_gitlab_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """Get GitLab user information."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://gitlab.com/api/v4/user",
                    headers={
                        "Authorization": f"Bearer {access_token}"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"GitLab user info request failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"GitLab user info error: {e}")
            return None

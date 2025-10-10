import os
import shutil
import tempfile
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import git
from git import Repo, InvalidGitRepositoryError, GitCommandError
import aiofiles
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.utils.parsers.diff_parser import DiffParser

logger = logging.getLogger(__name__)


class GitService:
    """Advanced Git repository operations service."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_code_review_repos"
        self.temp_dir.mkdir(exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.diff_parser = DiffParser()
        
        # Configure Git settings for operations
        self._configure_git_environment()
    
    def _configure_git_environment(self):
        """Configure Git environment for repository operations."""
        try:
            # Set up Git configuration for automated operations
            git_config = {
                'user.name': 'AI Code Review Bot',
                'user.email': 'bot@ai-code-review.local',
                'init.defaultBranch': 'main',
                'core.autocrlf': 'false',
                'core.filemode': 'false',
            }
            
            for key, value in git_config.items():
                try:
                    subprocess.run(
                        ['git', 'config', '--global', key, value],
                        capture_output=True,
                        check=True,
                        timeout=10
                    )
                except subprocess.SubprocessError as e:
                    logger.warning(f"Failed to set git config {key}: {e}")
                    
        except Exception as e:
            logger.error(f"Error configuring Git environment: {e}")
    
    async def prepare_repository(
        self,
        clone_url: str,
        branch: str = "main",
        commit_sha: Optional[str] = None,
        depth: Optional[int] = None,
        force_fresh: bool = False,
    ) -> str:
        """Clone or update repository for analysis."""
        try:
            # Generate unique repository path
            repo_name = self._extract_repo_name(clone_url)
            repo_path = self.temp_dir / f"{repo_name}_{hash(clone_url) % 10000}"
            
            # Remove existing repository if force_fresh or if it's corrupted
            if force_fresh or (repo_path.exists() and not self._is_valid_repository(str(repo_path))):
                if repo_path.exists():
                    await self._remove_directory_async(str(repo_path))
            
            # Clone repository if it doesn't exist
            if not repo_path.exists():
                logger.info(f"Cloning repository: {clone_url} to {repo_path}")
                await self._clone_repository_async(
                    clone_url, str(repo_path), branch, depth
                )
            else:
                logger.info(f"Updating existing repository: {repo_path}")
                await self._update_repository_async(str(repo_path), branch)
            
            # Checkout specific commit if provided
            if commit_sha:
                await self._checkout_commit_async(str(repo_path), commit_sha)
            
            return str(repo_path)
            
        except Exception as e:
            logger.error(f"Error preparing repository {clone_url}: {e}")
            raise
    
    async def _clone_repository_async(
        self,
        clone_url: str,
        repo_path: str,
        branch: str,
        depth: Optional[int] = None,
    ):
        """Asynchronously clone repository."""
        def _clone():
            try:
                # Build clone arguments
                clone_args = {
                    'url': clone_url,
                    'to_path': repo_path,
                    'branch': branch,
                    'single_branch': True,
                }
                
                if depth:
                    clone_args['depth'] = depth
                
                # Clone repository
                repo = Repo.clone_from(**clone_args)
                
                # Verify repository
                if not repo.git_dir:
                    raise InvalidGitRepositoryError(f"Failed to clone repository: {clone_url}")
                
                logger.info(f"Successfully cloned repository to {repo_path}")
                return repo
                
            except GitCommandError as e:
                logger.error(f"Git command error during clone: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during clone: {e}")
                raise
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _clone)
    
    async def _update_repository_async(self, repo_path: str, branch: str):
        """Asynchronously update existing repository."""
        def _update():
            try:
                repo = Repo(repo_path)
                
                # Fetch latest changes
                origin = repo.remotes.origin
                origin.fetch()
                
                # Checkout and pull the specified branch
                if branch in repo.heads:
                    repo.heads[branch].checkout()
                else:
                    # Create and track remote branch
                    if f'origin/{branch}' in [ref.name for ref in repo.refs]:
                        repo.create_head(branch, f'origin/{branch}')
                        repo.heads[branch].set_tracking_branch(origin.refs[branch])
                        repo.heads[branch].checkout()
                
                # Pull latest changes
                origin.pull()
                
                logger.info(f"Successfully updated repository at {repo_path}")
                return repo
                
            except GitCommandError as e:
                logger.error(f"Git command error during update: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during update: {e}")
                raise
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _update)
    
    async def _checkout_commit_async(self, repo_path: str, commit_sha: str):
        """Asynchronously checkout specific commit."""
        def _checkout():
            try:
                repo = Repo(repo_path)
                repo.git.checkout(commit_sha)
                logger.info(f"Checked out commit {commit_sha} in {repo_path}")
                return repo
                
            except GitCommandError as e:
                logger.error(f"Git command error during checkout: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during checkout: {e}")
                raise
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _checkout)
    
    async def get_changed_files(
        self,
        repo_path: str,
        commit_sha: Optional[str] = None,
        base_commit: Optional[str] = None,
    ) -> List[str]:
        """Get list of changed files in repository."""
        try:
            def _get_files():
                repo = Repo(repo_path)
                
                if commit_sha and base_commit:
                    # Get files changed between specific commits
                    diff_index = repo.commit(base_commit).diff(repo.commit(commit_sha))
                elif commit_sha:
                    # Get files changed in specific commit
                    commit = repo.commit(commit_sha)
                    if commit.parents:
                        diff_index = commit.parents[0].diff(commit)
                    else:
                        # Initial commit - all files are new
                        diff_index = commit.diff(git.NULL_TREE)
                else:
                    # Get files in working directory vs HEAD
                    diff_index = repo.head.commit.diff(None)
                
                changed_files = []
                for diff_item in diff_index:
                    if diff_item.a_path:
                        changed_files.append(diff_item.a_path)
                    if diff_item.b_path and diff_item.b_path != diff_item.a_path:
                        changed_files.append(diff_item.b_path)
                
                return list(set(changed_files))  # Remove duplicates
            
            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(self.executor, _get_files)
            
            logger.info(f"Found {len(files)} changed files in {repo_path}")
            return files
            
        except Exception as e:
            logger.error(f"Error getting changed files: {e}")
            return []
    
    async def get_all_files(
        self,
        repo_path: str,
        extensions: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
    ) -> List[str]:
        """Get all files in repository matching criteria."""
        try:
            if exclude_dirs is None:
                exclude_dirs = ['.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', '.venv']
            
            if extensions is None:
                extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs']
            
            def _get_files():
                all_files = []
                repo_path_obj = Path(repo_path)
                
                for file_path in repo_path_obj.rglob('*'):
                    if file_path.is_file():
                        # Check if file is in excluded directory
                        if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                            continue
                        
                        # Check file extension
                        if extensions and file_path.suffix.lower() not in extensions:
                            continue
                        
                        # Get relative path from repository root
                        relative_path = file_path.relative_to(repo_path_obj)
                        all_files.append(str(relative_path))
                
                return all_files
            
            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(self.executor, _get_files)
            
            logger.info(f"Found {len(files)} files in {repo_path}")
            return files
            
        except Exception as e:
            logger.error(f"Error getting all files: {e}")
            return []
    
    async def read_file(self, repo_path: str, file_path: str) -> str:
        """Read file content from repository."""
        try:
            full_path = Path(repo_path) / file_path
            
            if not full_path.exists():
                logger.warning(f"File not found: {full_path}")
                return ""
            
            # Check file size (limit to 1MB for analysis)
            if full_path.stat().st_size > 1024 * 1024:
                logger.warning(f"File too large, skipping: {full_path}")
                return ""
            
            async with aiofiles.open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
                return content
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""
    
    async def get_file_history(
        self,
        repo_path: str,
        file_path: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get commit history for a specific file."""
        try:
            def _get_history():
                repo = Repo(repo_path)
                commits = list(repo.iter_commits(paths=file_path, max_count=limit))
                
                history = []
                for commit in commits:
                    history.append({
                        'sha': commit.hexsha,
                        'author': {
                            'name': commit.author.name,
                            'email': commit.author.email,
                        },
                        'committer': {
                            'name': commit.committer.name,
                            'email': commit.committer.email,
                        },
                        'message': commit.message.strip(),
                        'date': commit.committed_datetime.isoformat(),
                        'stats': commit.stats.files.get(file_path, {}),
                    })
                
                return history
            
            loop = asyncio.get_event_loop()
            history = await loop.run_in_executor(self.executor, _get_history)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting file history for {file_path}: {e}")
            return []
    
    async def get_repository_stats(self, repo_path: str) -> Dict[str, Any]:
        """Get comprehensive repository statistics."""
        try:
            def _get_stats():
                repo = Repo(repo_path)
                
                # Basic repository info
                stats = {
                    'total_commits': 0,
                    'total_files': 0,
                    'total_lines': 0,
                    'languages': {},
                    'contributors': {},
                    'branches': [],
                    'tags': [],
                    'last_commit': None,
                    'first_commit': None,
                    'activity_by_month': {},
                    'file_types': {},
                }
                
                # Get all commits
                commits = list(repo.iter_commits())
                stats['total_commits'] = len(commits)
                
                if commits:
                    # Last and first commit info
                    last_commit = commits[0]
                    first_commit = commits[-1]
                    
                    stats['last_commit'] = {
                        'sha': last_commit.hexsha,
                        'date': last_commit.committed_datetime.isoformat(),
                        'author': last_commit.author.name,
                        'message': last_commit.message.strip()[:100],
                    }
                    
                    stats['first_commit'] = {
                        'sha': first_commit.hexsha,
                        'date': first_commit.committed_datetime.isoformat(),
                        'author': first_commit.author.name,
                        'message': first_commit.message.strip()[:100],
                    }
                
                # Analyze contributors
                for commit in commits:
                    author_email = commit.author.email
                    if author_email not in stats['contributors']:
                        stats['contributors'][author_email] = {
                            'name': commit.author.name,
                            'commits': 0,
                            'first_commit': commit.committed_datetime.isoformat(),
                            'last_commit': commit.committed_datetime.isoformat(),
                        }
                    
                    stats['contributors'][author_email]['commits'] += 1
                    
                    # Update activity by month
                    month_key = commit.committed_datetime.strftime('%Y-%m')
                    stats['activity_by_month'][month_key] = stats['activity_by_month'].get(month_key, 0) + 1
                
                # Get branches and tags
                stats['branches'] = [branch.name for branch in repo.branches]
                stats['tags'] = [tag.name for tag in repo.tags]
                
                return stats
            
            loop = asyncio.get_event_loop()
            base_stats = await loop.run_in_executor(self.executor, _get_stats)
            
            # Analyze files in working directory
            files = await self.get_all_files(repo_path)
            base_stats['total_files'] = len(files)
            
            # Analyze file types and languages
            for file_path in files:
                full_path = Path(repo_path) / file_path
                extension = full_path.suffix.lower()
                
                if extension:
                    base_stats['file_types'][extension] = base_stats['file_types'].get(extension, 0) + 1
                    
                    # Map extensions to languages
                    language = self._extension_to_language(extension)
                    if language:
                        base_stats['languages'][language] = base_stats['languages'].get(language, 0) + 1
                
                # Count lines for code files
                if self._is_code_extension(extension):
                    try:
                        content = await self.read_file(repo_path, file_path)
                        base_stats['total_lines'] += len(content.split('\n'))
                    except Exception:
                        continue
            
            return base_stats
            
        except Exception as e:
            logger.error(f"Error getting repository stats: {e}")
            return {}
    
    async def get_diff_between_commits(
        self,
        repo_path: str,
        commit1: str,
        commit2: str,
        file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get diff between two commits."""
        try:
            def _get_diff():
                repo = Repo(repo_path)
                
                commit1_obj = repo.commit(commit1)
                commit2_obj = repo.commit(commit2)
                
                if file_path:
                    diff_index = commit1_obj.diff(commit2_obj, paths=[file_path], create_patch=True)
                else:
                    diff_index = commit1_obj.diff(commit2_obj, create_patch=True)
                
                diff_data = {
                    'commit1': {
                        'sha': commit1_obj.hexsha,
                        'date': commit1_obj.committed_datetime.isoformat(),
                        'author': commit1_obj.author.name,
                        'message': commit1_obj.message.strip(),
                    },
                    'commit2': {
                        'sha': commit2_obj.hexsha,
                        'date': commit2_obj.committed_datetime.isoformat(),
                        'author': commit2_obj.author.name,
                        'message': commit2_obj.message.strip(),
                    },
                    'files': [],
                }
                
                for diff_item in diff_index:
                    file_diff = {
                        'file_path': diff_item.b_path or diff_item.a_path,
                        'old_file': diff_item.a_path,
                        'new_file': diff_item.b_path,
                        'change_type': self._get_change_type(diff_item),
                        'additions': 0,
                        'deletions': 0,
                        'patch': str(diff_item) if diff_item.diff else None,
                    }
                    
                    # Count additions/deletions
                    if diff_item.diff:
                        patch_text = diff_item.diff.decode('utf-8', errors='ignore')
                        additions, deletions = self._count_diff_lines(patch_text)
                        file_diff['additions'] = additions
                        file_diff['deletions'] = deletions
                    
                    diff_data['files'].append(file_diff)
                
                return diff_data
            
            loop = asyncio.get_event_loop()
            diff_data = await loop.run_in_executor(self.executor, _get_diff)
            
            return diff_data
            
        except Exception as e:
            logger.error(f"Error getting diff between commits: {e}")
            return {}
    
    async def get_commit_info(self, repo_path: str, commit_sha: str) -> Dict[str, Any]:
        """Get detailed information about a specific commit."""
        try:
            def _get_commit():
                repo = Repo(repo_path)
                commit = repo.commit(commit_sha)
                
                commit_info = {
                    'sha': commit.hexsha,
                    'short_sha': commit.hexsha[:8],
                    'author': {
                        'name': commit.author.name,
                        'email': commit.author.email,
                        'date': commit.authored_datetime.isoformat(),
                    },
                    'committer': {
                        'name': commit.committer.name,
                        'email': commit.committer.email,
                        'date': commit.committed_datetime.isoformat(),
                    },
                    'message': commit.message.strip(),
                    'parents': [parent.hexsha for parent in commit.parents],
                    'stats': {
                        'total_files': commit.stats.total['files'],
                        'total_insertions': commit.stats.total['insertions'],
                        'total_deletions': commit.stats.total['deletions'],
                        'files': commit.stats.files,
                    },
                    'modified_files': [],
                }
                
                # Get modified files
                if commit.parents:
                    diff_index = commit.parents[0].diff(commit)
                else:
                    diff_index = commit.diff(git.NULL_TREE)
                
                for diff_item in diff_index:
                    file_info = {
                        'file_path': diff_item.b_path or diff_item.a_path,
                        'change_type': self._get_change_type(diff_item),
                        'additions': 0,
                        'deletions': 0,
                    }
                    
                    # Get stats for this file
                    file_path = file_info['file_path']
                    if file_path in commit.stats.files:
                        file_stats = commit.stats.files[file_path]
                        file_info['additions'] = file_stats.get('insertions', 0)
                        file_info['deletions'] = file_stats.get('deletions', 0)
                    
                    commit_info['modified_files'].append(file_info)
                
                return commit_info
            
            loop = asyncio.get_event_loop()
            commit_info = await loop.run_in_executor(self.executor, _get_commit)
            
            return commit_info
            
        except Exception as e:
            logger.error(f"Error getting commit info for {commit_sha}: {e}")
            return {}
    
    async def get_branches(self, repo_path: str) -> List[Dict[str, Any]]:
        """Get all branches in repository."""
        try:
            def _get_branches():
                repo = Repo(repo_path)
                branches = []
                
                for branch in repo.branches:
                    branch_info = {
                        'name': branch.name,
                        'is_current': branch == repo.active_branch,
                        'commit': {
                            'sha': branch.commit.hexsha,
                            'date': branch.commit.committed_datetime.isoformat(),
                            'author': branch.commit.author.name,
                            'message': branch.commit.message.strip()[:100],
                        }
                    }
                    
                    # Check if branch tracks remote
                    if branch.tracking_branch():
                        branch_info['tracking'] = branch.tracking_branch().name
                    
                    branches.append(branch_info)
                
                return branches
            
            loop = asyncio.get_event_loop()
            branches = await loop.run_in_executor(self.executor, _get_branches)
            
            return branches
            
        except Exception as e:
            logger.error(f"Error getting branches: {e}")
            return []
    
    async def cleanup_repository(self, repo_path: str):
        """Clean up repository directory."""
        try:
            if os.path.exists(repo_path):
                await self._remove_directory_async(repo_path)
                logger.info(f"Cleaned up repository: {repo_path}")
                
        except Exception as e:
            logger.error(f"Error cleaning up repository {repo_path}: {e}")
    
    async def _remove_directory_async(self, directory_path: str):
        """Asynchronously remove directory."""
        def _remove():
            if os.path.exists(directory_path):
                shutil.rmtree(directory_path, ignore_errors=True)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _remove)
    
    def _extract_repo_name(self, clone_url: str) -> str:
        """Extract repository name from clone URL."""
        try:
            # Handle various URL formats
            if clone_url.endswith('.git'):
                clone_url = clone_url[:-4]
            
            repo_name = clone_url.split('/')[-1]
            
            # Clean the name for filesystem use
            import re
            repo_name = re.sub(r'[^a-zA-Z0-9_-]', '_', repo_name)
            
            return repo_name
            
        except Exception:
            return "unknown_repo"
    
    def _is_valid_repository(self, repo_path: str) -> bool:
        """Check if directory contains a valid Git repository."""
        try:
            Repo(repo_path)
            return True
        except (InvalidGitRepositoryError, Exception):
            return False
    
    def _get_change_type(self, diff_item) -> str:
        """Determine the type of change for a diff item."""
        if diff_item.new_file:
            return 'added'
        elif diff_item.deleted_file:
            return 'deleted'
        elif diff_item.renamed_file:
            return 'renamed'
        else:
            return 'modified'
    
    def _count_diff_lines(self, patch_text: str) -> Tuple[int, int]:
        """Count additions and deletions in a patch."""
        additions = 0
        deletions = 0
        
        for line in patch_text.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
        
        return additions, deletions
    
    def _extension_to_language(self, extension: str) -> Optional[str]:
        """Map file extension to programming language."""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'JavaScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.kt': 'Kotlin',
            '.swift': 'Swift',
            '.dart': 'Dart',
            '.scala': 'Scala',
            '.clj': 'Clojure',
            '.hs': 'Haskell',
            '.ml': 'OCaml',
            '.elm': 'Elm',
            '.ex': 'Elixir',
            '.erl': 'Erlang',
            '.lua': 'Lua',
            '.pl': 'Perl',
            '.r': 'R',
            '.jl': 'Julia',
            '.nim': 'Nim',
        }
        
        return language_map.get(extension.lower())
    
    def _is_code_extension(self, extension: str) -> bool:
        """Check if extension represents a code file."""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs',
            '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.dart', '.scala',
            '.clj', '.hs', '.ml', '.elm', '.ex', '.erl', '.lua', '.pl', '.r',
            '.jl', '.nim', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat',
            '.sql', '.html', '.css', '.scss', '.sass', '.less', '.xml',
            '.json', '.yaml', '.yml', '.toml', '.ini', '.conf',
        }
        
        return extension.lower() in code_extensions

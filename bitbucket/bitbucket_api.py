"""
Bitbucket API wrapper providing GitHub-compatible interface.
Implements all major repository operations for Bitbucket.
"""
import logging
import asyncio
import json
import base64
from typing import Dict, List, Optional, Any, Union
import aiohttp
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class BitbucketAPI:
    """Bitbucket API wrapper with GitHub-compatible interface."""
    
    def __init__(self, workspace: Optional[str] = None, username: Optional[str] = None, 
                 app_password: Optional[str] = None):
        """
        Initialize Bitbucket API client.
        
        Args:
            workspace: Bitbucket workspace (defaults to env var)
            username: Bitbucket username (defaults to env var)
            app_password: Bitbucket app password (defaults to env var)
        """
        self.workspace = workspace or os.environ.get('BITBUCKET_WORKSPACE')
        self.username = username or os.environ.get('BITBUCKET_USERNAME')
        self.app_password = app_password or os.environ.get('BITBUCKET_APP_PASSWORD')
        self.base_url = "https://api.bitbucket.org/2.0"
        self._session = None
        
        if not all([self.workspace, self.username, self.app_password]):
            raise ValueError("Bitbucket credentials not configured. Set BITBUCKET_WORKSPACE, BITBUCKET_USERNAME, and BITBUCKET_APP_PASSWORD")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self):
        """Initialize HTTP session with authentication."""
        if self._session:
            return
            
        self._session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self.username, self.app_password),
            headers={'Content-Type': 'application/json'}
        )
        
        # Test connection
        try:
            async with self._session.get(f"{self.base_url}/user") as response:
                if response.status != 200:
                    raise Exception(f"Failed to authenticate with Bitbucket: {response.status}")
                logger.info("Successfully connected to Bitbucket API")
        except Exception as e:
            await self.close()
            raise Exception(f"Failed to connect to Bitbucket API: {str(e)}")
    
    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    # Repository Management
    
    async def list_repositories(self, workspace: Optional[str] = None, 
                               page: int = 1, per_page: int = 30) -> Dict[str, Any]:
        """List repositories in workspace (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}"
        params = {'page': page, 'pagelen': per_page}
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                # Convert to GitHub-compatible format
                return {
                    'total_count': data.get('size', 0),
                    'items': [self._convert_repo_to_github_format(repo) for repo in data.get('values', [])]
                }
            else:
                raise Exception(f"Failed to list repositories: {response.status}")
    
    async def get_repository(self, workspace: Optional[str] = None, 
                           repo_slug: Optional[str] = None) -> Dict[str, Any]:
        """Get repository details (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}"
        
        async with self._session.get(url) as response:
            if response.status == 200:
                repo = await response.json()
                return self._convert_repo_to_github_format(repo)
            else:
                raise Exception(f"Failed to get repository: {response.status}")
    
    async def create_repository(self, name: str, workspace: Optional[str] = None,
                              description: str = "", is_private: bool = True,
                              scm: str = "git") -> Dict[str, Any]:
        """Create a new repository (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{name}"
        data = {
            'name': name,
            'description': description,
            'is_private': is_private,
            'scm': scm
        }
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                repo = await response.json()
                return self._convert_repo_to_github_format(repo)
            else:
                raise Exception(f"Failed to create repository: {response.status}")
    
    async def fork_repository(self, workspace: Optional[str] = None, 
                            repo_slug: Optional[str] = None,
                            organization: Optional[str] = None) -> Dict[str, Any]:
        """Fork a repository (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/forks"
        data = {}
        
        if organization:
            data['workspace'] = {'slug': organization}
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                repo = await response.json()
                return self._convert_repo_to_github_format(repo)
            else:
                raise Exception(f"Failed to fork repository: {response.status}")
    
    # File Operations
    
    async def get_file_contents(self, workspace: Optional[str] = None, 
                              repo_slug: Optional[str] = None,
                              path: str = "", ref: str = "main") -> Dict[str, Any]:
        """Get file contents from repository (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/src/{ref}/{path}"
        
        async with self._session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                return {
                    'type': 'file',
                    'name': path.split('/')[-1],
                    'path': path,
                    'content': content,
                    'encoding': 'utf-8',
                    'size': len(content.encode('utf-8'))
                }
            else:
                raise Exception(f"Failed to get file contents: {response.status}")
    
    async def create_or_update_file(self, workspace: Optional[str] = None,
                                  repo_slug: Optional[str] = None,
                                  path: str = "", content: Union[str, dict] = "",
                                  message: str = "", branch: str = "main",
                                  sha: Optional[str] = None) -> Dict[str, Any]:
        """Create or update a file in repository (GitHub-compatible)."""
        workspace = workspace or self.workspace
        
        # Convert dict content to JSON string
        if isinstance(content, dict):
            content = json.dumps(content, indent=2)
        
        # Bitbucket uses form data for file uploads
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/src"
        
        data = aiohttp.FormData()
        data.add_field('message', message)
        data.add_field('branch', branch)
        data.add_field(path, content)
        
        async with self._session.post(url, data=data) as response:
            if response.status in [200, 201]:
                result = await response.json()
                return {
                    'commit': {
                        'sha': result.get('hash', ''),
                        'message': message
                    },
                    'content': {
                        'path': path,
                        'sha': result.get('hash', ''),
                        'size': len(content.encode('utf-8'))
                    }
                }
            else:
                raise Exception(f"Failed to create/update file: {response.status}")
    
    async def push_files(self, workspace: Optional[str] = None,
                        repo_slug: Optional[str] = None,
                        branch: str = "main", files: List[Dict[str, str]] = None,
                        message: str = "") -> Dict[str, Any]:
        """Push multiple files in a single commit (GitHub-compatible)."""
        workspace = workspace or self.workspace
        files = files or []
        
        # Bitbucket doesn't support multi-file commits in a single API call
        # We'll commit files sequentially
        results = []
        
        for file_data in files:
            path = file_data.get('path', '')
            content = file_data.get('content', '')
            
            result = await self.create_or_update_file(
                workspace=workspace,
                repo_slug=repo_slug,
                path=path,
                content=content,
                message=f"{message} - {path}",
                branch=branch
            )
            results.append(result)
        
        # Return the last commit info
        if results:
            return results[-1]
        else:
            raise Exception("No files to push")
    
    # Issues Management
    
    async def list_issues(self, workspace: Optional[str] = None,
                         repo_slug: Optional[str] = None,
                         state: str = "new", labels: Optional[List[str]] = None,
                         page: int = 1, per_page: int = 30) -> Dict[str, Any]:
        """List issues in repository (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/issues"
        params = {'state': state, 'page': page, 'pagelen': per_page}
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'total_count': data.get('size', 0),
                    'items': [self._convert_issue_to_github_format(issue) for issue in data.get('values', [])]
                }
            else:
                raise Exception(f"Failed to list issues: {response.status}")
    
    async def get_issue(self, workspace: Optional[str] = None,
                       repo_slug: Optional[str] = None,
                       issue_id: int = 0) -> Dict[str, Any]:
        """Get issue details (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/issues/{issue_id}"
        
        async with self._session.get(url) as response:
            if response.status == 200:
                issue = await response.json()
                return self._convert_issue_to_github_format(issue)
            else:
                raise Exception(f"Failed to get issue: {response.status}")
    
    async def create_issue(self, workspace: Optional[str] = None,
                          repo_slug: Optional[str] = None,
                          title: str = "", body: str = "",
                          labels: Optional[List[str]] = None,
                          assignees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new issue (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/issues"
        data = {
            'title': title,
            'content': {'raw': body},
            'kind': 'bug',  # Default kind
            'priority': 'major'  # Default priority
        }
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                issue = await response.json()
                return self._convert_issue_to_github_format(issue)
            else:
                raise Exception(f"Failed to create issue: {response.status}")
    
    async def update_issue(self, workspace: Optional[str] = None,
                          repo_slug: Optional[str] = None,
                          issue_id: int = 0, title: Optional[str] = None,
                          body: Optional[str] = None, state: Optional[str] = None,
                          labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update an existing issue (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/issues/{issue_id}"
        data = {}
        
        if title is not None:
            data['title'] = title
        if body is not None:
            data['content'] = {'raw': body}
        if state is not None:
            data['state'] = state
        
        async with self._session.put(url, json=data) as response:
            if response.status == 200:
                issue = await response.json()
                return self._convert_issue_to_github_format(issue)
            else:
                raise Exception(f"Failed to update issue: {response.status}")
    
    async def add_issue_comment(self, workspace: Optional[str] = None,
                               repo_slug: Optional[str] = None,
                               issue_id: int = 0, body: str = "") -> Dict[str, Any]:
        """Add a comment to an issue (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/issues/{issue_id}/comments"
        data = {'content': {'raw': body}}
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                comment = await response.json()
                return self._convert_comment_to_github_format(comment)
            else:
                raise Exception(f"Failed to add issue comment: {response.status}")
    
    # Pull Requests Management
    
    async def list_pull_requests(self, workspace: Optional[str] = None,
                                repo_slug: Optional[str] = None,
                                state: str = "OPEN", page: int = 1,
                                per_page: int = 30) -> Dict[str, Any]:
        """List pull requests in repository (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests"
        params = {'state': state, 'page': page, 'pagelen': per_page}
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'total_count': data.get('size', 0),
                    'items': [self._convert_pr_to_github_format(pr) for pr in data.get('values', [])]
                }
            else:
                raise Exception(f"Failed to list pull requests: {response.status}")
    
    async def get_pull_request(self, workspace: Optional[str] = None,
                              repo_slug: Optional[str] = None,
                              pull_request_id: int = 0) -> Dict[str, Any]:
        """Get pull request details (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}"
        
        async with self._session.get(url) as response:
            if response.status == 200:
                pr = await response.json()
                return self._convert_pr_to_github_format(pr)
            else:
                raise Exception(f"Failed to get pull request: {response.status}")
    
    async def create_pull_request(self, workspace: Optional[str] = None,
                                 repo_slug: Optional[str] = None,
                                 title: str = "", body: str = "",
                                 head: str = "", base: str = "main",
                                 draft: bool = False) -> Dict[str, Any]:
        """Create a new pull request (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests"
        data = {
            'title': title,
            'description': body,
            'source': {'branch': {'name': head}},
            'destination': {'branch': {'name': base}}
        }
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                pr = await response.json()
                return self._convert_pr_to_github_format(pr)
            else:
                raise Exception(f"Failed to create pull request: {response.status}")
    
    async def update_pull_request(self, workspace: Optional[str] = None,
                                 repo_slug: Optional[str] = None,
                                 pull_request_id: int = 0,
                                 title: Optional[str] = None,
                                 body: Optional[str] = None,
                                 state: Optional[str] = None) -> Dict[str, Any]:
        """Update an existing pull request (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}"
        data = {}
        
        if title is not None:
            data['title'] = title
        if body is not None:
            data['description'] = body
        if state is not None:
            data['state'] = state
        
        async with self._session.put(url, json=data) as response:
            if response.status == 200:
                pr = await response.json()
                return self._convert_pr_to_github_format(pr)
            else:
                raise Exception(f"Failed to update pull request: {response.status}")
    
    async def merge_pull_request(self, workspace: Optional[str] = None,
                                repo_slug: Optional[str] = None,
                                pull_request_id: int = 0,
                                merge_method: str = "merge_commit") -> Dict[str, Any]:
        """Merge a pull request (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/merge"
        data = {'merge_strategy': merge_method}
        
        async with self._session.post(url, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    'merged': True,
                    'sha': result.get('hash', ''),
                    'message': 'Pull request merged successfully'
                }
            else:
                raise Exception(f"Failed to merge pull request: {response.status}")
    
    # Branches Management
    
    async def list_branches(self, workspace: Optional[str] = None,
                           repo_slug: Optional[str] = None,
                           page: int = 1, per_page: int = 30) -> Dict[str, Any]:
        """List branches in repository (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/refs/branches"
        params = {'page': page, 'pagelen': per_page}
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'total_count': data.get('size', 0),
                    'items': [self._convert_branch_to_github_format(branch) for branch in data.get('values', [])]
                }
            else:
                raise Exception(f"Failed to list branches: {response.status}")
    
    async def create_branch(self, workspace: Optional[str] = None,
                           repo_slug: Optional[str] = None,
                           branch: str = "", sha: str = "") -> Dict[str, Any]:
        """Create a new branch (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/refs/branches"
        data = {
            'name': branch,
            'target': {'hash': sha}
        }
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                branch_data = await response.json()
                return self._convert_branch_to_github_format(branch_data)
            else:
                raise Exception(f"Failed to create branch: {response.status}")
    
    # Commits Management
    
    async def list_commits(self, workspace: Optional[str] = None,
                          repo_slug: Optional[str] = None,
                          sha: Optional[str] = None, path: Optional[str] = None,
                          page: int = 1, per_page: int = 30) -> Dict[str, Any]:
        """List commits in repository (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/commits"
        params = {'page': page, 'pagelen': per_page}
        
        if sha:
            params['include'] = sha
        if path:
            params['path'] = path
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'total_count': data.get('size', 0),
                    'items': [self._convert_commit_to_github_format(commit) for commit in data.get('values', [])]
                }
            else:
                raise Exception(f"Failed to list commits: {response.status}")
    
    async def get_commit(self, workspace: Optional[str] = None,
                        repo_slug: Optional[str] = None,
                        sha: str = "") -> Dict[str, Any]:
        """Get commit details (GitHub-compatible)."""
        workspace = workspace or self.workspace
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/commit/{sha}"
        
        async with self._session.get(url) as response:
            if response.status == 200:
                commit = await response.json()
                return self._convert_commit_to_github_format(commit)
            else:
                raise Exception(f"Failed to get commit: {response.status}")
    
    # Format conversion methods
    
    def _convert_repo_to_github_format(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Bitbucket repository format to GitHub format."""
        return {
            'id': repo.get('uuid', ''),
            'name': repo.get('name', ''),
            'full_name': repo.get('full_name', ''),
            'description': repo.get('description', ''),
            'private': repo.get('is_private', False),
            'html_url': repo.get('links', {}).get('html', {}).get('href', ''),
            'clone_url': repo.get('links', {}).get('clone', [{}])[0].get('href', ''),
            'created_at': repo.get('created_on', ''),
            'updated_at': repo.get('updated_on', ''),
            'language': repo.get('language', ''),
            'size': repo.get('size', 0),
            'default_branch': repo.get('mainbranch', {}).get('name', 'main')
        }
    
    def _convert_issue_to_github_format(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Bitbucket issue format to GitHub format."""
        return {
            'id': issue.get('id', 0),
            'number': issue.get('id', 0),
            'title': issue.get('title', ''),
            'body': issue.get('content', {}).get('raw', ''),
            'state': issue.get('state', ''),
            'created_at': issue.get('created_on', ''),
            'updated_at': issue.get('updated_on', ''),
            'html_url': issue.get('links', {}).get('html', {}).get('href', ''),
            'user': {
                'login': issue.get('reporter', {}).get('username', ''),
                'html_url': issue.get('reporter', {}).get('links', {}).get('html', {}).get('href', '')
            }
        }
    
    def _convert_pr_to_github_format(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Bitbucket pull request format to GitHub format."""
        return {
            'id': pr.get('id', 0),
            'number': pr.get('id', 0),
            'title': pr.get('title', ''),
            'body': pr.get('description', ''),
            'state': pr.get('state', '').lower(),
            'created_at': pr.get('created_on', ''),
            'updated_at': pr.get('updated_on', ''),
            'html_url': pr.get('links', {}).get('html', {}).get('href', ''),
            'head': {
                'ref': pr.get('source', {}).get('branch', {}).get('name', ''),
                'sha': pr.get('source', {}).get('commit', {}).get('hash', '')
            },
            'base': {
                'ref': pr.get('destination', {}).get('branch', {}).get('name', ''),
                'sha': pr.get('destination', {}).get('commit', {}).get('hash', '')
            },
            'user': {
                'login': pr.get('author', {}).get('username', ''),
                'html_url': pr.get('author', {}).get('links', {}).get('html', {}).get('href', '')
            }
        }
    
    def _convert_branch_to_github_format(self, branch: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Bitbucket branch format to GitHub format."""
        return {
            'name': branch.get('name', ''),
            'commit': {
                'sha': branch.get('target', {}).get('hash', ''),
                'url': branch.get('target', {}).get('links', {}).get('html', {}).get('href', '')
            },
            'protected': False  # Bitbucket doesn't provide this info easily
        }
    
    def _convert_commit_to_github_format(self, commit: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Bitbucket commit format to GitHub format."""
        return {
            'sha': commit.get('hash', ''),
            'commit': {
                'message': commit.get('message', ''),
                'author': {
                    'name': commit.get('author', {}).get('raw', ''),
                    'email': '',  # Not easily available in Bitbucket
                    'date': commit.get('date', '')
                }
            },
            'html_url': commit.get('links', {}).get('html', {}).get('href', ''),
            'author': {
                'login': commit.get('author', {}).get('user', {}).get('username', ''),
                'html_url': commit.get('author', {}).get('user', {}).get('links', {}).get('html', {}).get('href', '')
            }
        }
    
    def _convert_comment_to_github_format(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Bitbucket comment format to GitHub format."""
        return {
            'id': comment.get('id', 0),
            'body': comment.get('content', {}).get('raw', ''),
            'created_at': comment.get('created_on', ''),
            'updated_at': comment.get('updated_on', ''),
            'html_url': comment.get('links', {}).get('html', {}).get('href', ''),
            'user': {
                'login': comment.get('user', {}).get('username', ''),
                'html_url': comment.get('user', {}).get('links', {}).get('html', {}).get('href', '')
            }
        }
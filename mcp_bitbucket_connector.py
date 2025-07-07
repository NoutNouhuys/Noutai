"""
Bitbucket MCP Connector module.
Handles communication with Bitbucket API through MCP protocol.
"""
import logging
import asyncio
import json
import base64
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import aiohttp
import os

logger = logging.getLogger(__name__)


@dataclass
class BitbucketToolResult:
    """Result from Bitbucket tool execution."""
    content: Any
    is_error: bool = False


class BitbucketMCPConnector:
    """Bitbucket MCP connector that mimics GitHub MCP server functionality."""
    
    def __init__(self):
        """Initialize Bitbucket MCP connector."""
        self.workspace = os.environ.get('BITBUCKET_WORKSPACE')
        self.username = os.environ.get('BITBUCKET_USERNAME')
        self.app_password = os.environ.get('BITBUCKET_APP_PASSWORD')
        self.base_url = "https://api.bitbucket.org/2.0"
        self._session = None
        self._connected = False
        
    async def connect_to_server(self, script_path: Optional[str] = None, venv_path: Optional[str] = None) -> None:
        """
        Connect to Bitbucket API (simulates MCP server connection).
        
        Args:
            script_path: Not used for Bitbucket (kept for compatibility)
            venv_path: Not used for Bitbucket (kept for compatibility)
        """
        if not all([self.workspace, self.username, self.app_password]):
            raise ValueError("Bitbucket credentials not configured. Set BITBUCKET_WORKSPACE, BITBUCKET_USERNAME, and BITBUCKET_APP_PASSWORD")
        
        # Create HTTP session with authentication
        self._session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self.username, self.app_password),
            headers={'Content-Type': 'application/json'}
        )
        
        # Test connection
        try:
            async with self._session.get(f"{self.base_url}/user") as response:
                if response.status == 200:
                    self._connected = True
                    logger.info("Successfully connected to Bitbucket API")
                else:
                    raise Exception(f"Failed to authenticate with Bitbucket: {response.status}")
        except Exception as e:
            await self._session.close()
            self._session = None
            raise Exception(f"Failed to connect to Bitbucket API: {str(e)}")
    
    async def close(self) -> None:
        """Close connection to Bitbucket API."""
        if self._session:
            await self._session.close()
            self._session = None
            self._connected = False
            logger.info("Disconnected from Bitbucket API")
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get available Bitbucket tools (equivalent to GitHub MCP tools).
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "list_bitbucket_repositories",
                "description": "List repositories in Bitbucket workspace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "page": {"type": "integer", "default": 1},
                        "per_page": {"type": "integer", "default": 30}
                    },
                    "required": ["workspace"]
                }
            },
            {
                "name": "create_bitbucket_repository",
                "description": "Create a new Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "name": {"type": "string", "description": "Repository name"},
                        "description": {"type": "string", "default": ""},
                        "is_private": {"type": "boolean", "default": True},
                        "scm": {"type": "string", "default": "git"}
                    },
                    "required": ["workspace", "name"]
                }
            },
            {
                "name": "get_bitbucket_file_contents",
                "description": "Get contents of a file from Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "path": {"type": "string", "description": "File path"},
                        "ref": {"type": "string", "default": "main", "description": "Branch or commit"}
                    },
                    "required": ["workspace", "repo_slug", "path"]
                }
            },
            {
                "name": "create_or_update_bitbucket_file",
                "description": "Create or update a file in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "File content"},
                        "message": {"type": "string", "description": "Commit message"},
                        "branch": {"type": "string", "default": "main", "description": "Target branch"}
                    },
                    "required": ["workspace", "repo_slug", "path", "content", "message"]
                }
            },
            {
                "name": "list_bitbucket_issues",
                "description": "List issues in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "state": {"type": "string", "default": "new", "description": "Issue state"},
                        "page": {"type": "integer", "default": 1},
                        "per_page": {"type": "integer", "default": 30}
                    },
                    "required": ["workspace", "repo_slug"]
                }
            },
            {
                "name": "create_bitbucket_issue",
                "description": "Create a new issue in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "title": {"type": "string", "description": "Issue title"},
                        "content": {"type": "string", "default": "", "description": "Issue content"},
                        "kind": {"type": "string", "default": "bug", "description": "Issue kind"},
                        "priority": {"type": "string", "default": "major", "description": "Issue priority"}
                    },
                    "required": ["workspace", "repo_slug", "title"]
                }
            },
            {
                "name": "update_bitbucket_issue",
                "description": "Update an existing issue in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "issue_id": {"type": "integer", "description": "Issue ID"},
                        "title": {"type": "string", "description": "Issue title"},
                        "content": {"type": "string", "description": "Issue content"},
                        "state": {"type": "string", "description": "Issue state"},
                        "kind": {"type": "string", "description": "Issue kind"},
                        "priority": {"type": "string", "description": "Issue priority"}
                    },
                    "required": ["workspace", "repo_slug", "issue_id"]
                }
            },
            {
                "name": "list_bitbucket_pull_requests",
                "description": "List pull requests in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "state": {"type": "string", "default": "OPEN", "description": "PR state"},
                        "page": {"type": "integer", "default": 1},
                        "per_page": {"type": "integer", "default": 30}
                    },
                    "required": ["workspace", "repo_slug"]
                }
            },
            {
                "name": "create_bitbucket_pull_request",
                "description": "Create a new pull request in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "title": {"type": "string", "description": "PR title"},
                        "description": {"type": "string", "default": "", "description": "PR description"},
                        "source_branch": {"type": "string", "description": "Source branch"},
                        "destination_branch": {"type": "string", "default": "main", "description": "Destination branch"}
                    },
                    "required": ["workspace", "repo_slug", "title", "source_branch"]
                }
            },
            {
                "name": "merge_bitbucket_pull_request",
                "description": "Merge a pull request in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "pull_request_id": {"type": "integer", "description": "Pull request ID"},
                        "merge_strategy": {"type": "string", "default": "merge_commit", "description": "Merge strategy"}
                    },
                    "required": ["workspace", "repo_slug", "pull_request_id"]
                }
            },
            {
                "name": "list_bitbucket_branches",
                "description": "List branches in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "page": {"type": "integer", "default": 1},
                        "per_page": {"type": "integer", "default": 30}
                    },
                    "required": ["workspace", "repo_slug"]
                }
            },
            {
                "name": "create_bitbucket_branch",
                "description": "Create a new branch in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "name": {"type": "string", "description": "Branch name"},
                        "target": {"type": "string", "description": "Target commit or branch"}
                    },
                    "required": ["workspace", "repo_slug", "name", "target"]
                }
            }
        ]
    
    async def use_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> BitbucketToolResult:
        """
        Execute a Bitbucket tool.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            
        Returns:
            BitbucketToolResult with execution result
        """
        if not self._connected:
            return BitbucketToolResult(
                content="Not connected to Bitbucket API",
                is_error=True
            )
        
        try:
            # Route to appropriate method based on tool name
            if tool_name == "list_bitbucket_repositories":
                result = await self._list_repositories(tool_args)
            elif tool_name == "create_bitbucket_repository":
                result = await self._create_repository(tool_args)
            elif tool_name == "get_bitbucket_file_contents":
                result = await self._get_file_contents(tool_args)
            elif tool_name == "create_or_update_bitbucket_file":
                result = await self._create_or_update_file(tool_args)
            elif tool_name == "list_bitbucket_issues":
                result = await self._list_issues(tool_args)
            elif tool_name == "create_bitbucket_issue":
                result = await self._create_issue(tool_args)
            elif tool_name == "update_bitbucket_issue":
                result = await self._update_issue(tool_args)
            elif tool_name == "list_bitbucket_pull_requests":
                result = await self._list_pull_requests(tool_args)
            elif tool_name == "create_bitbucket_pull_request":
                result = await self._create_pull_request(tool_args)
            elif tool_name == "merge_bitbucket_pull_request":
                result = await self._merge_pull_request(tool_args)
            elif tool_name == "list_bitbucket_branches":
                result = await self._list_branches(tool_args)
            elif tool_name == "create_bitbucket_branch":
                result = await self._create_branch(tool_args)
            else:
                return BitbucketToolResult(
                    content=f"Unknown tool: {tool_name}",
                    is_error=True
                )
            
            return BitbucketToolResult(content=result)
            
        except Exception as e:
            logger.error(f"Error executing Bitbucket tool {tool_name}: {str(e)}")
            return BitbucketToolResult(
                content=f"Error executing {tool_name}: {str(e)}",
                is_error=True
            )
    
    async def _list_repositories(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List repositories in workspace."""
        workspace = args.get('workspace', self.workspace)
        page = args.get('page', 1)
        per_page = args.get('per_page', 30)
        
        url = f"{self.base_url}/repositories/{workspace}"
        params = {'page': page, 'pagelen': per_page}
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to list repositories: {response.status}")
    
    async def _create_repository(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new repository."""
        workspace = args.get('workspace', self.workspace)
        name = args['name']
        description = args.get('description', '')
        is_private = args.get('is_private', True)
        scm = args.get('scm', 'git')
        
        url = f"{self.base_url}/repositories/{workspace}/{name}"
        data = {
            'name': name,
            'description': description,
            'is_private': is_private,
            'scm': scm
        }
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                raise Exception(f"Failed to create repository: {response.status}")
    
    async def _get_file_contents(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get file contents from repository."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        path = args['path']
        ref = args.get('ref', 'main')
        
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/src/{ref}/{path}"
        
        async with self._session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                return {
                    'type': 'file',
                    'path': path,
                    'content': content,
                    'encoding': 'utf-8'
                }
            else:
                raise Exception(f"Failed to get file contents: {response.status}")
    
    async def _create_or_update_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a file in repository."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        path = args['path']
        content = args['content']
        message = args['message']
        branch = args.get('branch', 'main')
        
        # Bitbucket uses form data for file uploads
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/src"
        
        data = aiohttp.FormData()
        data.add_field('message', message)
        data.add_field('branch', branch)
        data.add_field(path, content)
        
        async with self._session.post(url, data=data) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                raise Exception(f"Failed to create/update file: {response.status}")
    
    async def _list_issues(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List issues in repository."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        state = args.get('state', 'new')
        page = args.get('page', 1)
        per_page = args.get('per_page', 30)
        
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/issues"
        params = {'state': state, 'page': page, 'pagelen': per_page}
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to list issues: {response.status}")
    
    async def _create_issue(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        title = args['title']
        content = args.get('content', '')
        kind = args.get('kind', 'bug')
        priority = args.get('priority', 'major')
        
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/issues"
        data = {
            'title': title,
            'content': {'raw': content},
            'kind': kind,
            'priority': priority
        }
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                raise Exception(f"Failed to create issue: {response.status}")
    
    async def _update_issue(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing issue."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        issue_id = args['issue_id']
        
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/issues/{issue_id}"
        data = {}
        
        if 'title' in args:
            data['title'] = args['title']
        if 'content' in args:
            data['content'] = {'raw': args['content']}
        if 'state' in args:
            data['state'] = args['state']
        if 'kind' in args:
            data['kind'] = args['kind']
        if 'priority' in args:
            data['priority'] = args['priority']
        
        async with self._session.put(url, json=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to update issue: {response.status}")
    
    async def _list_pull_requests(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List pull requests in repository."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        state = args.get('state', 'OPEN')
        page = args.get('page', 1)
        per_page = args.get('per_page', 30)
        
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests"
        params = {'state': state, 'page': page, 'pagelen': per_page}
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to list pull requests: {response.status}")
    
    async def _create_pull_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pull request."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        title = args['title']
        description = args.get('description', '')
        source_branch = args['source_branch']
        destination_branch = args.get('destination_branch', 'main')
        
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests"
        data = {
            'title': title,
            'description': description,
            'source': {'branch': {'name': source_branch}},
            'destination': {'branch': {'name': destination_branch}}
        }
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                raise Exception(f"Failed to create pull request: {response.status}")
    
    async def _merge_pull_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a pull request."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        pull_request_id = args['pull_request_id']
        merge_strategy = args.get('merge_strategy', 'merge_commit')
        
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/merge"
        data = {'merge_strategy': merge_strategy}
        
        async with self._session.post(url, json=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to merge pull request: {response.status}")
    
    async def _list_branches(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List branches in repository."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        page = args.get('page', 1)
        per_page = args.get('per_page', 30)
        
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/refs/branches"
        params = {'page': page, 'pagelen': per_page}
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to list branches: {response.status}")
    
    async def _create_branch(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new branch."""
        workspace = args.get('workspace', self.workspace)
        repo_slug = args['repo_slug']
        name = args['name']
        target = args['target']
        
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/refs/branches"
        data = {
            'name': name,
            'target': {'hash': target}
        }
        
        async with self._session.post(url, json=data) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                raise Exception(f"Failed to create branch: {response.status}")
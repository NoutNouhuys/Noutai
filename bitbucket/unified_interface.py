"""
Unified interface for multi-platform repository operations.
Provides a single interface that works with both GitHub and Bitbucket.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from .bitbucket_api import BitbucketAPI
from .platform_detector import PlatformDetector

logger = logging.getLogger(__name__)


class UnifiedInterface:
    """Unified interface for GitHub and Bitbucket operations."""
    
    def __init__(self, github_connector=None, bitbucket_api: Optional[BitbucketAPI] = None,
                 default_platform: str = "github"):
        """
        Initialize unified interface.
        
        Args:
            github_connector: GitHub MCP connector instance
            bitbucket_api: Bitbucket API instance
            default_platform: Default platform to use
        """
        self.github_connector = github_connector
        self.bitbucket_api = bitbucket_api
        self.detector = PlatformDetector(default_platform)
        self._github_connected = False
        self._bitbucket_connected = False
    
    async def connect(self, platform: Optional[str] = None) -> bool:
        """
        Connect to specified platform(s).
        
        Args:
            platform: Specific platform to connect to, or None for all
            
        Returns:
            True if at least one connection successful
        """
        success = False
        
        if platform is None or platform == self.detector.PLATFORM_GITHUB:
            if self.github_connector:
                try:
                    # GitHub connector connection logic would go here
                    # This depends on the specific MCP connector implementation
                    self._github_connected = True
                    success = True
                    logger.info("Connected to GitHub via MCP connector")
                except Exception as e:
                    logger.error(f"Failed to connect to GitHub: {str(e)}")
        
        if platform is None or platform == self.detector.PLATFORM_BITBUCKET:
            if self.bitbucket_api:
                try:
                    await self.bitbucket_api.connect()
                    self._bitbucket_connected = True
                    success = True
                    logger.info("Connected to Bitbucket API")
                except Exception as e:
                    logger.error(f"Failed to connect to Bitbucket: {str(e)}")
        
        return success
    
    async def disconnect(self, platform: Optional[str] = None) -> None:
        """
        Disconnect from specified platform(s).
        
        Args:
            platform: Specific platform to disconnect from, or None for all
        """
        if platform is None or platform == self.detector.PLATFORM_GITHUB:
            if self.github_connector and self._github_connected:
                try:
                    # GitHub connector disconnection logic would go here
                    self._github_connected = False
                    logger.info("Disconnected from GitHub")
                except Exception as e:
                    logger.error(f"Error disconnecting from GitHub: {str(e)}")
        
        if platform is None or platform == self.detector.PLATFORM_BITBUCKET:
            if self.bitbucket_api and self._bitbucket_connected:
                try:
                    await self.bitbucket_api.close()
                    self._bitbucket_connected = False
                    logger.info("Disconnected from Bitbucket")
                except Exception as e:
                    logger.error(f"Error disconnecting from Bitbucket: {str(e)}")
    
    def is_connected(self, platform: Optional[str] = None) -> bool:
        """
        Check if connected to platform(s).
        
        Args:
            platform: Specific platform to check, or None for any
            
        Returns:
            True if connected to specified platform(s)
        """
        if platform == self.detector.PLATFORM_GITHUB:
            return self._github_connected
        elif platform == self.detector.PLATFORM_BITBUCKET:
            return self._bitbucket_connected
        else:
            return self._github_connected or self._bitbucket_connected
    
    def get_connected_platforms(self) -> List[str]:
        """Get list of connected platforms."""
        platforms = []
        if self._github_connected:
            platforms.append(self.detector.PLATFORM_GITHUB)
        if self._bitbucket_connected:
            platforms.append(self.detector.PLATFORM_BITBUCKET)
        return platforms
    
    async def execute_tool(self, tool_name: str, tool_args: Dict[str, Any],
                          platform: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a tool on the appropriate platform.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            platform: Optional platform override
            
        Returns:
            Tool execution result
        """
        # Detect target platform
        target_platform = platform or self.detector.detect_platform(
            tool_name=tool_name, **tool_args
        )
        
        # Normalize arguments for target platform
        normalized_args = self.detector.normalize_repo_args(target_platform, **tool_args)
        
        # Get platform-specific tool name
        platform_tool_name = self.detector.get_platform_specific_tool_name(
            tool_name, target_platform
        )
        
        logger.debug(f"Executing {platform_tool_name} on {target_platform}")
        
        try:
            if target_platform == self.detector.PLATFORM_GITHUB:
                return await self._execute_github_tool(platform_tool_name, normalized_args)
            elif target_platform == self.detector.PLATFORM_BITBUCKET:
                return await self._execute_bitbucket_tool(platform_tool_name, normalized_args)
            else:
                raise ValueError(f"Unsupported platform: {target_platform}")
        
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "platform": target_platform,
                "tool_name": platform_tool_name
            }
    
    async def _execute_github_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool on GitHub platform."""
        if not self._github_connected:
            raise RuntimeError("Not connected to GitHub")
        
        if not self.github_connector:
            raise RuntimeError("GitHub connector not available")
        
        # Execute tool via GitHub MCP connector
        result = await self.github_connector.use_tool(tool_name=tool_name, tool_args=tool_args)
        
        return {
            "success": True,
            "content": result.content,
            "platform": self.detector.PLATFORM_GITHUB,
            "tool_name": tool_name
        }
    
    async def _execute_bitbucket_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool on Bitbucket platform."""
        if not self._bitbucket_connected:
            raise RuntimeError("Not connected to Bitbucket")
        
        if not self.bitbucket_api:
            raise RuntimeError("Bitbucket API not available")
        
        # Map tool name to Bitbucket API method
        result = await self._call_bitbucket_method(tool_name, tool_args)
        
        return {
            "success": True,
            "content": result,
            "platform": self.detector.PLATFORM_BITBUCKET,
            "tool_name": tool_name
        }
    
    async def _call_bitbucket_method(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Call appropriate Bitbucket API method based on tool name."""
        # Repository operations
        if tool_name in ['list_bitbucket_repositories', 'list_repositories']:
            return await self.bitbucket_api.list_repositories(**tool_args)
        elif tool_name in ['get_bitbucket_repository', 'get_repository']:
            return await self.bitbucket_api.get_repository(**tool_args)
        elif tool_name in ['create_bitbucket_repository', 'create_repository']:
            return await self.bitbucket_api.create_repository(**tool_args)
        elif tool_name in ['fork_bitbucket_repository', 'fork_repository']:
            return await self.bitbucket_api.fork_repository(**tool_args)
        
        # File operations
        elif tool_name in ['get_bitbucket_file_contents', 'get_file_contents']:
            return await self.bitbucket_api.get_file_contents(**tool_args)
        elif tool_name in ['create_or_update_bitbucket_file', 'create_or_update_file']:
            return await self.bitbucket_api.create_or_update_file(**tool_args)
        elif tool_name in ['push_bitbucket_files', 'push_files']:
            return await self.bitbucket_api.push_files(**tool_args)
        
        # Issue operations
        elif tool_name in ['list_bitbucket_issues', 'list_issues']:
            return await self.bitbucket_api.list_issues(**tool_args)
        elif tool_name in ['get_bitbucket_issue', 'get_issue']:
            return await self.bitbucket_api.get_issue(**tool_args)
        elif tool_name in ['create_bitbucket_issue', 'create_issue']:
            return await self.bitbucket_api.create_issue(**tool_args)
        elif tool_name in ['update_bitbucket_issue', 'update_issue']:
            return await self.bitbucket_api.update_issue(**tool_args)
        elif tool_name in ['add_bitbucket_issue_comment', 'add_issue_comment']:
            return await self.bitbucket_api.add_issue_comment(**tool_args)
        
        # Pull request operations
        elif tool_name in ['list_bitbucket_pull_requests', 'list_pull_requests']:
            return await self.bitbucket_api.list_pull_requests(**tool_args)
        elif tool_name in ['get_bitbucket_pull_request', 'get_pull_request']:
            return await self.bitbucket_api.get_pull_request(**tool_args)
        elif tool_name in ['create_bitbucket_pull_request', 'create_pull_request']:
            return await self.bitbucket_api.create_pull_request(**tool_args)
        elif tool_name in ['update_bitbucket_pull_request', 'update_pull_request']:
            return await self.bitbucket_api.update_pull_request(**tool_args)
        elif tool_name in ['merge_bitbucket_pull_request', 'merge_pull_request']:
            return await self.bitbucket_api.merge_pull_request(**tool_args)
        
        # Branch operations
        elif tool_name in ['list_bitbucket_branches', 'list_branches']:
            return await self.bitbucket_api.list_branches(**tool_args)
        elif tool_name in ['create_bitbucket_branch', 'create_branch']:
            return await self.bitbucket_api.create_branch(**tool_args)
        
        # Commit operations
        elif tool_name in ['list_bitbucket_commits', 'list_commits']:
            return await self.bitbucket_api.list_commits(**tool_args)
        elif tool_name in ['get_bitbucket_commit', 'get_commit']:
            return await self.bitbucket_api.get_commit(**tool_args)
        
        else:
            raise ValueError(f"Unknown Bitbucket tool: {tool_name}")
    
    async def get_available_tools(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available tools for specified platform(s).
        
        Args:
            platform: Specific platform or None for all connected platforms
            
        Returns:
            List of available tools
        """
        tools = []
        
        if platform is None or platform == self.detector.PLATFORM_GITHUB:
            if self._github_connected and self.github_connector:
                try:
                    github_tools = await self.github_connector.get_tools()
                    tools.extend(github_tools)
                except Exception as e:
                    logger.error(f"Failed to get GitHub tools: {str(e)}")
        
        if platform is None or platform == self.detector.PLATFORM_BITBUCKET:
            if self._bitbucket_connected and self.bitbucket_api:
                try:
                    bitbucket_tools = self._get_bitbucket_tools()
                    tools.extend(bitbucket_tools)
                except Exception as e:
                    logger.error(f"Failed to get Bitbucket tools: {str(e)}")
        
        return tools
    
    def _get_bitbucket_tools(self) -> List[Dict[str, Any]]:
        """Get list of available Bitbucket tools."""
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
                    }
                }
            },
            {
                "name": "get_bitbucket_repository",
                "description": "Get Bitbucket repository details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"}
                    },
                    "required": ["workspace", "repo_slug"]
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
                        "is_private": {"type": "boolean", "default": True}
                    },
                    "required": ["workspace", "name"]
                }
            },
            {
                "name": "get_bitbucket_file_contents",
                "description": "Get file contents from Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "path": {"type": "string", "description": "File path"},
                        "ref": {"type": "string", "default": "main"}
                    },
                    "required": ["workspace", "repo_slug", "path"]
                }
            },
            {
                "name": "create_or_update_bitbucket_file",
                "description": "Create or update file in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "File content"},
                        "message": {"type": "string", "description": "Commit message"},
                        "branch": {"type": "string", "default": "main"}
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
                        "state": {"type": "string", "default": "new"},
                        "page": {"type": "integer", "default": 1},
                        "per_page": {"type": "integer", "default": 30}
                    },
                    "required": ["workspace", "repo_slug"]
                }
            },
            {
                "name": "create_bitbucket_issue",
                "description": "Create new issue in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "title": {"type": "string", "description": "Issue title"},
                        "body": {"type": "string", "default": "", "description": "Issue body"}
                    },
                    "required": ["workspace", "repo_slug", "title"]
                }
            },
            {
                "name": "update_bitbucket_issue",
                "description": "Update existing issue in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "issue_id": {"type": "integer", "description": "Issue ID"},
                        "title": {"type": "string", "description": "Issue title"},
                        "body": {"type": "string", "description": "Issue body"},
                        "state": {"type": "string", "description": "Issue state"}
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
                        "state": {"type": "string", "default": "OPEN"},
                        "page": {"type": "integer", "default": 1},
                        "per_page": {"type": "integer", "default": 30}
                    },
                    "required": ["workspace", "repo_slug"]
                }
            },
            {
                "name": "create_bitbucket_pull_request",
                "description": "Create new pull request in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "title": {"type": "string", "description": "PR title"},
                        "body": {"type": "string", "default": "", "description": "PR description"},
                        "head": {"type": "string", "description": "Source branch"},
                        "base": {"type": "string", "default": "main", "description": "Target branch"}
                    },
                    "required": ["workspace", "repo_slug", "title", "head"]
                }
            },
            {
                "name": "merge_bitbucket_pull_request",
                "description": "Merge pull request in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "pull_request_id": {"type": "integer", "description": "Pull request ID"},
                        "merge_method": {"type": "string", "default": "merge_commit"}
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
                "description": "Create new branch in Bitbucket repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace": {"type": "string", "description": "Bitbucket workspace"},
                        "repo_slug": {"type": "string", "description": "Repository slug"},
                        "branch": {"type": "string", "description": "Branch name"},
                        "sha": {"type": "string", "description": "Source commit SHA"}
                    },
                    "required": ["workspace", "repo_slug", "branch", "sha"]
                }
            }
        ]
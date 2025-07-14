import logging
import asyncio
import os
from typing import Dict, List, Optional, Any, Callable
from mcp_connector import MCPConnector
from anthropic_config import AnthropicConfig

logger = logging.getLogger(__name__)

class MCPIntegration:
    """Manages MCP server connections and tool usage."""

    def __init__(self, config: AnthropicConfig):
        """
        Initialize MCP integration.

        Args:
            config: AnthropicConfig instance
        """
        self.config = config
        self.connector = MCPConnector()
        self.connected = False
        self.available_tool_names = []

    async def connect(self):
        """Connect to MCP server as configured."""
        if self.connected:
            return

        await self.connector.connect_to_server(
            server_script_path=os.getenv("MCP_SERVER_SCRIPT"),
            python_executable_path=os.getenv("MCP_SERVER_VENV_PATH")
        )
        self.connected = True

        tools = await self.connector.get_tools()
        self.available_tool_names = [tool["name"] for tool in tools]
        logger.info(f"Connected with tools: {self.available_tool_names}")

    async def disconnect(self):
        """Disconnect from the MCP server."""
        await self.connector.close()
        self.connected = False

    async def list_projects(self) -> List[Dict[str, Any]]:
        """List GitHub or Bitbucket projects/repos (depending on available tools)."""
        await self.connect()

        if "get_projects" in self.available_tool_names:
            return await self.connector.use_tool("get_projects", {})
        elif "list_repositories" in self.available_tool_names:
            return await self.connector.use_tool("list_repositories", {})
        else:
            raise ValueError("No tool available to list projects or repositories")

    async def list_repositories(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """List repositories for GitHub (no project key) or Bitbucket (with project key)."""
        await self.connect()

        if "list_repositories" in self.available_tool_names:
            args = {"project_key": project_key} if project_key else {}
            return await self.connector.use_tool("list_repositories", args)

        raise ValueError("No tool available to list repositories")

    async def get_repository_info(self, project_key: Optional[str], repo_slug: str) -> Dict[str, Any]:
        """Get detailed repository info."""
        await self.connect()

        if "get_repo_info" in self.available_tool_names:
            return await self.connector.use_tool("get_repo_info", {
                "project_key": project_key,
                "repo_slug": repo_slug
            })

        raise ValueError("No tool available to fetch repository info")

    async def list_pull_requests(self, project_key: Optional[str], repo_slug: str) -> List[Dict[str, Any]]:
        await self.connect()

        if "list_pull_requests" in self.available_tool_names:
            return await self.connector.use_tool("list_pull_requests", {
                "project_key": project_key,
                "repo_slug": repo_slug
            })

        raise ValueError("No tool available to list pull requests")

    async def create_pull_request(self, project_key: Optional[str], repo_slug: str, title: str,
                                   source_branch: str, target_branch: str, description: str = "") -> Dict[str, Any]:
        await self.connect()

        if "create_pull_request" in self.available_tool_names:
            return await self.connector.use_tool("create_pull_request", {
                "project_key": project_key,
                "repo_slug": repo_slug,
                "title": title,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "description": description
            })

        raise ValueError("No tool available to create pull request")

    async def list_branches(self, project_key: Optional[str], repo_slug: str) -> List[Dict[str, Any]]:
        await self.connect()

        if "list_branches" in self.available_tool_names:
            return await self.connector.use_tool("list_branches", {
                "project_key": project_key,
                "repo_slug": repo_slug
            })

        raise ValueError("No tool available to list branches")

    async def get_commits(self, project_key: Optional[str], repo_slug: str, branch: str = "master") -> List[Dict[str, Any]]:
        await self.connect()

        if "get_commits" in self.available_tool_names:
            return await self.connector.use_tool("get_commits", {
                "project_key": project_key,
                "repo_slug": repo_slug,
                "branch": branch
            })

        raise ValueError("No tool available to get commits")

    @property
    def is_connected(self) -> bool:
        """Compatibility alias for connected flag."""
        return self.connected

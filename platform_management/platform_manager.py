"""
Platform Manager

Manages multi-platform Git repository support, including automatic platform detection,
routing to appropriate connectors, and unified tool interface.
"""
import logging
import re
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from anthropic_config import AnthropicConfig
from mcp_integration import MCPIntegration
from .mcp_bitbucket_connector import MCPBitbucketConnector

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported Git platforms."""
    GITHUB = "github"
    BITBUCKET = "bitbucket"
    AUTO = "auto"


class PlatformManager:
    """
    Manages multi-platform Git repository operations.
    
    Provides unified interface for GitHub and Bitbucket operations,
    with automatic platform detection and routing.
    """
    
    def __init__(self, config: AnthropicConfig):
        """
        Initialize Platform Manager.
        
        Args:
            config: AnthropicConfig instance
        """
        self.config = config
        self.github_connector = MCPIntegration(config)
        self.bitbucket_connector = MCPBitbucketConnector(config)
        self.active_platform = Platform.AUTO
        self._github_connected = False
        self._bitbucket_connected = False
        
    async def initialize(self) -> Dict[str, bool]:
        """
        Initialize all platform connectors.
        
        Returns:
            Dict with connection status for each platform
        """
        results = {}
        
        # Initialize GitHub connector
        try:
            self._github_connected = await self.github_connector.connect()
            results["github"] = self._github_connected
            if self._github_connected:
                logger.info("GitHub MCP connector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub connector: {str(e)}")
            results["github"] = False
            
        # Initialize Bitbucket connector
        try:
            self._bitbucket_connected = await self.bitbucket_connector.connect()
            results["bitbucket"] = self._bitbucket_connected
            if self._bitbucket_connected:
                logger.info("Bitbucket MCP connector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bitbucket connector: {str(e)}")
            results["bitbucket"] = False
            
        return results
        
    async def disconnect_all(self) -> None:
        """Disconnect from all platform connectors."""
        if self._github_connected:
            await self.github_connector.disconnect()
            self._github_connected = False
            
        if self._bitbucket_connected:
            await self.bitbucket_connector.disconnect()
            self._bitbucket_connected = False
            
    def detect_platform(self, repository_identifier: str) -> Platform:
        """
        Detect platform from repository identifier.
        
        Args:
            repository_identifier: Repository identifier (owner/repo, URL, etc.)
            
        Returns:
            Detected platform
        """
        # GitHub patterns
        github_patterns = [
            r'github\\.com',
            r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$',  # Simple owner/repo format
            r'git@github\\.com:',
            r'https://github\\.com/'
        ]
        
        # Bitbucket patterns
        bitbucket_patterns = [
            r'bitbucket\\.org',
            r'git@bitbucket\\.org:',
            r'https://bitbucket\\.org/',
            r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$'  # Could be Bitbucket workspace/repo
        ]
        
        # Check for explicit platform indicators
        for pattern in github_patterns[:-1]:  # Exclude generic pattern
            if re.search(pattern, repository_identifier, re.IGNORECASE):
                return Platform.GITHUB
                
        for pattern in bitbucket_patterns[:-1]:  # Exclude generic pattern
            if re.search(pattern, repository_identifier, re.IGNORECASE):
                return Platform.BITBUCKET
                
        # If no explicit indicators, default to GitHub for simple owner/repo format
        if re.match(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$', repository_identifier):
            return Platform.GITHUB
            
        return Platform.AUTO
        
    def set_active_platform(self, platform: Union[Platform, str]) -> bool:
        """
        Set the active platform.
        
        Args:
            platform: Platform to set as active
            
        Returns:
            True if platform was set successfully
        """
        if isinstance(platform, str):
            try:
                platform = Platform(platform.lower())
            except ValueError:
                logger.error(f"Invalid platform: {platform}")
                return False
                
        if platform == Platform.GITHUB and not self._github_connected:
            logger.error("Cannot set GitHub as active platform - not connected")
            return False
            
        if platform == Platform.BITBUCKET and not self._bitbucket_connected:
            logger.error("Cannot set Bitbucket as active platform - not connected")
            return False
            
        self.active_platform = platform
        logger.info(f"Active platform set to: {platform.value}")
        return True
        
    def get_active_platform(self) -> Platform:
        """Get the currently active platform."""
        return self.active_platform
        
    def get_connection_status(self) -> Dict[str, bool]:
        """
        Get connection status for all platforms.
        
        Returns:
            Dict with connection status for each platform
        """
        return {
            "github": self._github_connected,
            "bitbucket": self._bitbucket_connected
        }
        
    def get_available_platforms(self) -> List[str]:
        """
        Get list of available (connected) platforms.
        
        Returns:
            List of available platform names
        """
        available = []
        if self._github_connected:
            available.append("github")
        if self._bitbucket_connected:
            available.append("bitbucket")
        return available
        
    async def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get tools from all connected platforms.
        
        Returns:
            Dict with tools grouped by platform
        """
        all_tools = {}
        
        if self._github_connected:
            github_tools = await self.github_connector.get_tools()
            for tool in github_tools:
                tool["platform"] = "github"
            all_tools["github"] = github_tools
            
        if self._bitbucket_connected:
            bitbucket_tools = await self.bitbucket_connector.get_tools()
            all_tools["bitbucket"] = bitbucket_tools
            
        return all_tools
        
    async def get_unified_tools(self) -> List[Dict[str, Any]]:
        """
        Get unified tool list from all platforms.
        
        Returns:
            List of all available tools with platform identifiers
        """
        all_tools = await self.get_all_tools()
        unified_tools = []
        
        for platform, tools in all_tools.items():
            unified_tools.extend(tools)
            
        return unified_tools
        
    def _determine_platform_for_tool(
        self, 
        tool_name: str, 
        tool_args: Dict[str, Any], 
        repository_hint: Optional[str] = None
    ) -> Platform:
        """
        Determine which platform to use for a tool execution.
        
        Args:
            tool_name: Name of the tool
            tool_args: Tool arguments
            repository_hint: Optional repository identifier hint
            
        Returns:
            Platform to use for tool execution
        """
        # If active platform is explicitly set (not AUTO), use it
        if self.active_platform != Platform.AUTO:
            return self.active_platform
            
        # Try to detect from repository hint
        if repository_hint:
            detected = self.detect_platform(repository_hint)
            if detected != Platform.AUTO:
                return detected
                
        # Try to detect from tool arguments
        repo_identifiers = []
        
        # GitHub-style arguments
        if "owner" in tool_args and "repo" in tool_args:
            repo_identifiers.append(f"{tool_args['owner']}/{tool_args['repo']}")
            
        # Bitbucket-style arguments
        if "workspace" in tool_args and "repo_slug" in tool_args:
            repo_identifiers.append(f"{tool_args['workspace']}/{tool_args['repo_slug']}")
            
        # Check other common repository fields
        for field in ["repository", "repo_name", "project"]:
            if field in tool_args:
                repo_identifiers.append(str(tool_args[field]))
                
        # Try to detect platform from repository identifiers
        for repo_id in repo_identifiers:
            detected = self.detect_platform(repo_id)
            if detected != Platform.AUTO:
                return detected
                
        # Default to GitHub if both are available, or the only available platform
        if self._github_connected and self._bitbucket_connected:
            return Platform.GITHUB
        elif self._github_connected:
            return Platform.GITHUB
        elif self._bitbucket_connected:
            return Platform.BITBUCKET
        else:
            raise RuntimeError("No platforms are connected")
            
    async def use_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        platform: Optional[Union[Platform, str]] = None,
        repository_hint: Optional[str] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool on the appropriate platform.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            platform: Optional platform override
            repository_hint: Optional repository identifier hint
            log_callback: Optional callback for logging
            
        Returns:
            Tool execution result with platform information
        """
        try:
            # Determine platform to use
            if platform:
                if isinstance(platform, str):
                    platform = Platform(platform.lower())
                target_platform = platform
            else:
                target_platform = self._determine_platform_for_tool(
                    tool_name, tool_args, repository_hint
                )
                
            # Execute tool on appropriate platform
            if target_platform == Platform.GITHUB:
                if not self._github_connected:
                    raise RuntimeError("GitHub connector is not connected")
                result = await self.github_connector.use_tool(tool_name, tool_args, log_callback)
                result["platform"] = "github"
                
            elif target_platform == Platform.BITBUCKET:
                if not self._bitbucket_connected:
                    raise RuntimeError("Bitbucket connector is not connected")
                result = await self.bitbucket_connector.use_tool(tool_name, tool_args, log_callback)
                result["platform"] = "bitbucket"
                
            else:
                raise RuntimeError(f"Unsupported platform: {target_platform}")
                
            logger.info(f"Tool '{tool_name}' executed successfully on {result['platform']}")
            return result
            
        except Exception as e:
            error_msg = f"Platform tool execution failed: {str(e)}"
            logger.error(error_msg)
            
            if log_callback:
                log_callback(f"✗ Platform tool execution failed:\\n  Error: {str(e)}")
                
            return {
                "success": False, 
                "error": str(e), 
                "content": error_msg,
                "platform": "unknown"
            }
            
    def convert_github_to_bitbucket_args(self, tool_name: str, github_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert GitHub tool arguments to Bitbucket format.
        
        Args:
            tool_name: Name of the tool
            github_args: GitHub-style arguments
            
        Returns:
            Bitbucket-style arguments
        """
        bitbucket_args = github_args.copy()
        
        # Convert owner/repo to workspace/repo_slug
        if "owner" in github_args and "repo" in github_args:
            bitbucket_args["workspace"] = github_args["owner"]
            bitbucket_args["repo_slug"] = github_args["repo"]
            del bitbucket_args["owner"]
            del bitbucket_args["repo"]
            
        # Convert GitHub-specific fields
        if tool_name == "create_pull_request":
            if "head" in github_args:
                bitbucket_args["source_branch"] = github_args["head"]
                del bitbucket_args["head"]
            if "base" in github_args:
                bitbucket_args["destination_branch"] = github_args["base"]
                del bitbucket_args["base"]
                
        elif tool_name == "merge_pull_request":
            if "pull_number" in github_args:
                bitbucket_args["pull_request_id"] = github_args["pull_number"]
                del bitbucket_args["pull_number"]
            if "merge_method" in github_args:
                # Convert GitHub merge methods to Bitbucket
                method_mapping = {
                    "merge": "merge_commit",
                    "squash": "squash",
                    "rebase": "fast_forward"
                }
                bitbucket_args["merge_strategy"] = method_mapping.get(
                    github_args["merge_method"], "merge_commit"
                )
                del bitbucket_args["merge_method"]
                
        elif tool_name == "update_issue":
            if "issue_number" in github_args:
                bitbucket_args["issue_id"] = github_args["issue_number"]
                del bitbucket_args["issue_number"]
                
        elif tool_name == "create_repository":
            if "private" in github_args:
                bitbucket_args["is_private"] = github_args["private"]
                del bitbucket_args["private"]
                
        return bitbucket_args
        
    def convert_bitbucket_to_github_args(self, tool_name: str, bitbucket_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Bitbucket tool arguments to GitHub format.
        
        Args:
            tool_name: Name of the tool
            bitbucket_args: Bitbucket-style arguments
            
        Returns:
            GitHub-style arguments
        """
        github_args = bitbucket_args.copy()
        
        # Convert workspace/repo_slug to owner/repo
        if "workspace" in bitbucket_args and "repo_slug" in bitbucket_args:
            github_args["owner"] = bitbucket_args["workspace"]
            github_args["repo"] = bitbucket_args["repo_slug"]
            del github_args["workspace"]
            del github_args["repo_slug"]
            
        # Convert Bitbucket-specific fields
        if tool_name == "create_pull_request":
            if "source_branch" in bitbucket_args:
                github_args["head"] = bitbucket_args["source_branch"]
                del github_args["source_branch"]
            if "destination_branch" in bitbucket_args:
                github_args["base"] = bitbucket_args["destination_branch"]
                del github_args["destination_branch"]
                
        elif tool_name == "merge_pull_request":
            if "pull_request_id" in bitbucket_args:
                github_args["pull_number"] = bitbucket_args["pull_request_id"]
                del github_args["pull_request_id"]
            if "merge_strategy" in bitbucket_args:
                # Convert Bitbucket merge strategies to GitHub
                strategy_mapping = {
                    "merge_commit": "merge",
                    "squash": "squash",
                    "fast_forward": "rebase"
                }
                github_args["merge_method"] = strategy_mapping.get(
                    bitbucket_args["merge_strategy"], "merge"
                )
                del github_args["merge_strategy"]
                
        elif tool_name == "update_issue":
            if "issue_id" in bitbucket_args:
                github_args["issue_number"] = bitbucket_args["issue_id"]
                del github_args["issue_id"]
                
        elif tool_name == "create_repository":
            if "is_private" in bitbucket_args:
                github_args["private"] = bitbucket_args["is_private"]
                del github_args["is_private"]
                
        return github_args
"""
MCP (Model Context Protocol) integration module.
Handles communication with MCP servers for tool usage.
Supports both GitHub and Bitbucket platforms.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
import mcp_connector
import mcp_bitbucket_connector
from anthropic_config import AnthropicConfig

logger = logging.getLogger(__name__)


class MCPIntegration:
    """Manages MCP server connections and tool usage for multiple platforms."""
    
    def __init__(self, config: AnthropicConfig):
        """
        Initialize MCP integration.
        
        Args:
            config: AnthropicConfig instance
        """
        self.config = config
        self.github_connector = mcp_connector.MCPConnector()
        self.bitbucket_connector = mcp_bitbucket_connector.BitbucketMCPConnector()
        self._github_connected = False
        self._bitbucket_connected = False
        self._active_platform = None
        
    async def connect(self, 
                     platform: Optional[str] = None,
                     server_script_path: Optional[str] = None, 
                     server_venv_path: Optional[str] = None) -> bool:
        """
        Connect to MCP server(s).
        
        Args:
            platform: Specific platform to connect to (github/bitbucket), or None for all configured
            server_script_path: Path to server script (GitHub only)
            server_venv_path: Path to virtual environment (GitHub only)
            
        Returns:
            True if at least one connection successful
        """
        success = False
        
        # Determine which platforms to connect to
        platforms_to_connect = []
        if platform:
            if self.config.is_platform_supported(platform):
                platforms_to_connect = [platform.lower()]
            else:
                logger.error(f"Unsupported platform: {platform}")
                return False
        else:
            # Connect to all configured platforms
            if self.config.is_github_configured():
                platforms_to_connect.append(self.config.PLATFORM_GITHUB)
            if self.config.is_bitbucket_configured():
                platforms_to_connect.append(self.config.PLATFORM_BITBUCKET)
        
        # Connect to GitHub if requested and configured
        if self.config.PLATFORM_GITHUB in platforms_to_connect:
            try:
                script_path = server_script_path or self.config.mcp_server_script
                venv_path = server_venv_path or self.config.mcp_server_venv_path
                
                if script_path:
                    await self.github_connector.connect_to_server(script_path, venv_path)
                    self._github_connected = True
                    success = True
                    logger.info("Successfully connected to GitHub MCP server")
                else:
                    logger.debug("GitHub MCP server script path not configured")
                    
            except Exception as e:
                logger.error(f"Failed to connect to GitHub MCP server: {str(e)}")
        
        # Connect to Bitbucket if requested and configured
        if self.config.PLATFORM_BITBUCKET in platforms_to_connect:
            try:
                if self.config.is_bitbucket_configured():
                    await self.bitbucket_connector.connect_to_server()
                    self._bitbucket_connected = True
                    success = True
                    logger.info("Successfully connected to Bitbucket API")
                else:
                    logger.debug("Bitbucket API not configured")
                    
            except Exception as e:
                logger.error(f"Failed to connect to Bitbucket API: {str(e)}")
        
        # Set active platform
        if success:
            if platform:
                self._active_platform = platform.lower()
            else:
                # Use default platform if multiple are connected
                self._active_platform = self.config.default_platform
                
        return success
            
    async def disconnect(self) -> None:
        """Disconnect from all MCP servers."""
        if self._github_connected:
            try:
                await self.github_connector.close()
                self._github_connected = False
                logger.info("Disconnected from GitHub MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from GitHub MCP server: {str(e)}")
        
        if self._bitbucket_connected:
            try:
                await self.bitbucket_connector.close()
                self._bitbucket_connected = False
                logger.info("Disconnected from Bitbucket API")
            except Exception as e:
                logger.error(f"Error disconnecting from Bitbucket API: {str(e)}")
                
        self._active_platform = None
                
    async def get_tools(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available tools from MCP server(s).
        
        Args:
            platform: Specific platform to get tools from, or None for all connected
        
        Returns:
            List of tool definitions
        """
        tools = []
        
        # Determine which platforms to get tools from
        if platform:
            platforms = [platform.lower()] if self.config.is_platform_supported(platform) else []
        else:
            platforms = []
            if self._github_connected:
                platforms.append(self.config.PLATFORM_GITHUB)
            if self._bitbucket_connected:
                platforms.append(self.config.PLATFORM_BITBUCKET)
        
        # Get GitHub tools
        if self.config.PLATFORM_GITHUB in platforms and self._github_connected:
            try:
                github_tools = await self.github_connector.get_tools()
                tools.extend(github_tools)
                logger.debug(f"Retrieved {len(github_tools)} tools from GitHub MCP server")
            except Exception as e:
                logger.error(f"Failed to get tools from GitHub MCP server: {str(e)}")
        
        # Get Bitbucket tools
        if self.config.PLATFORM_BITBUCKET in platforms and self._bitbucket_connected:
            try:
                bitbucket_tools = await self.bitbucket_connector.get_tools()
                tools.extend(bitbucket_tools)
                logger.debug(f"Retrieved {len(bitbucket_tools)} tools from Bitbucket connector")
            except Exception as e:
                logger.error(f"Failed to get tools from Bitbucket connector: {str(e)}")
        
        # Remove duplicates (though there shouldn't be any with different prefixes)
        unique_tools = []
        seen = set()
        for tool in tools:
            if tool["name"] not in seen:
                unique_tools.append(tool)
                seen.add(tool["name"])
                
        logger.debug(f"Retrieved {len(unique_tools)} unique tools total")
        return unique_tools
    
    def _detect_platform_from_tool(self, tool_name: str) -> Optional[str]:
        """
        Detect platform from tool name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Platform name or None if cannot be detected
        """
        if tool_name.startswith('bitbucket_') or 'bitbucket' in tool_name:
            return self.config.PLATFORM_BITBUCKET
        elif any(github_tool in tool_name for github_tool in [
            'get_file_contents', 'create_issue', 'list_issues', 'create_pull_request',
            'list_pull_requests', 'merge_pull_request', 'create_repository', 'fork_repository',
            'create_branch', 'list_branches', 'create_or_update_file', 'push_files'
        ]):
            return self.config.PLATFORM_GITHUB
        return None
    
    def _detect_platform_from_args(self, tool_args: Dict[str, Any]) -> Optional[str]:
        """
        Detect platform from tool arguments.
        
        Args:
            tool_args: Tool arguments
            
        Returns:
            Platform name or None if cannot be detected
        """
        # Bitbucket uses workspace/repo_slug pattern
        if 'workspace' in tool_args and 'repo_slug' in tool_args:
            return self.config.PLATFORM_BITBUCKET
        # GitHub uses owner/repo pattern
        elif 'owner' in tool_args and 'repo' in tool_args:
            return self.config.PLATFORM_GITHUB
        return None
    
    def _convert_github_to_bitbucket_args(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert GitHub tool arguments to Bitbucket format.
        
        Args:
            tool_name: Name of the tool
            tool_args: GitHub tool arguments
            
        Returns:
            Converted Bitbucket tool arguments
        """
        converted_args = tool_args.copy()
        
        # Convert owner/repo to workspace/repo_slug
        if 'owner' in converted_args:
            converted_args['workspace'] = converted_args.pop('owner')
        if 'repo' in converted_args:
            converted_args['repo_slug'] = converted_args.pop('repo')
        
        # Convert specific argument names
        if 'issue_number' in converted_args:
            converted_args['issue_id'] = converted_args.pop('issue_number')
        if 'pull_number' in converted_args:
            converted_args['pull_request_id'] = converted_args.pop('pull_number')
        if 'body' in converted_args:
            converted_args['content'] = converted_args.pop('body')
        if 'head' in converted_args:
            converted_args['source_branch'] = converted_args.pop('head')
        if 'base' in converted_args:
            converted_args['destination_branch'] = converted_args.pop('base')
        
        return converted_args
    
    def _convert_github_to_bitbucket_tool_name(self, tool_name: str) -> str:
        """
        Convert GitHub tool name to Bitbucket equivalent.
        
        Args:
            tool_name: GitHub tool name
            
        Returns:
            Bitbucket tool name
        """
        # Mapping of GitHub tools to Bitbucket tools
        tool_mapping = {
            'get_file_contents': 'get_bitbucket_file_contents',
            'create_issue': 'create_bitbucket_issue',
            'update_issue': 'update_bitbucket_issue',
            'list_issues': 'list_bitbucket_issues',
            'create_pull_request': 'create_bitbucket_pull_request',
            'list_pull_requests': 'list_bitbucket_pull_requests',
            'merge_pull_request': 'merge_bitbucket_pull_request',
            'create_repository': 'create_bitbucket_repository',
            'list_repositories': 'list_bitbucket_repositories',
            'create_branch': 'create_bitbucket_branch',
            'list_branches': 'list_bitbucket_branches',
            'create_or_update_file': 'create_or_update_bitbucket_file'
        }
        
        return tool_mapping.get(tool_name, tool_name)
    
    def _format_tool_args(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Format tool arguments for readable logging."""
        if tool_name.startswith('get_') and 'file_contents' in tool_name:
            if 'workspace' in tool_args:
                # Bitbucket format
                repo_info = f"{tool_args.get('workspace', 'unknown')}/{tool_args.get('repo_slug', 'unknown')}"
            else:
                # GitHub format
                repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            path = tool_args.get('path', 'unknown')
            ref = tool_args.get('ref', 'main')
            return f"  Repository: {repo_info}\n  Path: {path}\n  Branch/Ref: {ref}"
        
        elif 'create_issue' in tool_name or 'create_bitbucket_issue' in tool_name:
            if 'workspace' in tool_args:
                repo_info = f"{tool_args.get('workspace', 'unknown')}/{tool_args.get('repo_slug', 'unknown')}"
            else:
                repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            title = tool_args.get('title', 'No title')
            labels = tool_args.get('labels', [])
            return f"  Repository: {repo_info}\n  Title: {title}\n  Labels: {', '.join(labels) if labels else 'None'}"
        
        elif 'update_issue' in tool_name:
            if 'workspace' in tool_args:
                repo_info = f"{tool_args.get('workspace', 'unknown')}/{tool_args.get('repo_slug', 'unknown')}"
                issue_num = tool_args.get('issue_id', 'unknown')
            else:
                repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
                issue_num = tool_args.get('issue_number', 'unknown')
            title = tool_args.get('title', 'No title change')
            state = tool_args.get('state', 'No state change')
            return f"  Repository: {repo_info}\n  Issue: #{issue_num}\n  Title: {title}\n  State: {state}"
        
        elif 'create_pull_request' in tool_name or 'create_bitbucket_pull_request' in tool_name:
            if 'workspace' in tool_args:
                repo_info = f"{tool_args.get('workspace', 'unknown')}/{tool_args.get('repo_slug', 'unknown')}"
                head = tool_args.get('source_branch', 'unknown')
                base = tool_args.get('destination_branch', 'unknown')
            else:
                repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
                head = tool_args.get('head', 'unknown')
                base = tool_args.get('base', 'unknown')
            title = tool_args.get('title', 'No title')
            return f"  Repository: {repo_info}\n  Title: {title}\n  From: {head} → {base}"
        
        elif 'merge_pull_request' in tool_name:
            if 'workspace' in tool_args:
                repo_info = f"{tool_args.get('workspace', 'unknown')}/{tool_args.get('repo_slug', 'unknown')}"
                pr_num = tool_args.get('pull_request_id', 'unknown')
                method = tool_args.get('merge_strategy', 'merge')
            else:
                repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
                pr_num = tool_args.get('pull_number', 'unknown')
                method = tool_args.get('merge_method', 'merge')
            return f"  Repository: {repo_info}\n  Pull Request: #{pr_num}\n  Method: {method}"
        
        elif 'create_or_update_file' in tool_name:
            if 'workspace' in tool_args:
                repo_info = f"{tool_args.get('workspace', 'unknown')}/{tool_args.get('repo_slug', 'unknown')}"
            else:
                repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            path = tool_args.get('path', 'unknown')
            branch = tool_args.get('branch', 'main')
            content_size = len(str(tool_args.get('content', '')))
            return f"  Repository: {repo_info}\n  Path: {path}\n  Branch: {branch}\n  Content size: {content_size} chars"
        
        elif 'list_issues' in tool_name:
            if 'workspace' in tool_args:
                repo_info = f"{tool_args.get('workspace', 'unknown')}/{tool_args.get('repo_slug', 'unknown')}"
            else:
                repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            state = tool_args.get('state', 'open')
            labels = tool_args.get('labels', [])
            return f"  Repository: {repo_info}\n  State: {state}\n  Labels: {', '.join(labels) if labels else 'All'}"
        
        else:
            # Generic formatting for unknown tools
            formatted_args = []
            for key, value in tool_args.items():
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                formatted_args.append(f"  {key}: {value}")
            return "\n".join(formatted_args) if formatted_args else "  No parameters"
    
    def _summarize_result(self, tool_name: str, content: Any) -> str:
        """Make a concise summary of the result."""
        if not content:
            return "  No result content"
        
        content_str = str(content)
        
        # Tool-specific result summaries
        if 'file_contents' in tool_name:
            try:
                if "type" in content_str and "content" in content_str:
                    content_length = len(content_str)
                    file_type = "text" if "text" in content_str else "binary"
                    return f"  File retrieved ({content_length/1024:.1f} KB)\n  Type: {file_type}"
                else:
                    return f"  File content retrieved ({len(content_str)} chars)"
            except:
                return f"  File content retrieved ({len(content_str)} chars)"
        
        elif 'issue' in tool_name and ('create' in tool_name or 'update' in tool_name):
            if "id" in content_str or "number" in content_str:
                try:
                    import re
                    # Try to find issue ID or number
                    match = re.search(r'"(?:id|number)":\s*(\d+)', content_str)
                    if match:
                        issue_num = match.group(1)
                        return f"  Issue #{issue_num} processed successfully"
                except:
                    pass
            return "  Issue processed successfully"
        
        elif 'pull_request' in tool_name and 'create' in tool_name:
            if "id" in content_str or "number" in content_str:
                try:
                    import re
                    match = re.search(r'"(?:id|number)":\s*(\d+)', content_str)
                    if match:
                        pr_num = match.group(1)
                        return f"  Pull Request #{pr_num} created"
                except:
                    pass
            return "  Pull Request created successfully"
        
        elif 'merge' in tool_name and 'pull_request' in tool_name:
            if "merged" in content_str:
                return "  Pull Request merged successfully"
            return "  Pull Request merge processed"
        
        elif 'create_or_update_file' in tool_name:
            if "commit" in content_str:
                try:
                    import re
                    match = re.search(r'"(?:sha|hash)":\s*"([a-f0-9]{7})', content_str)
                    if match:
                        sha = match.group(1)
                        return f"  Files committed (SHA: {sha})"
                except:
                    pass
            return "  Files committed successfully"
        
        elif 'list' in tool_name:
            try:
                import re
                # Count items in list result
                matches = re.findall(r'"(?:id|number)":', content_str)
                count = len(matches)
                if 'issue' in tool_name:
                    item_type = "issues"
                elif 'pull_request' in tool_name:
                    item_type = "pull requests"
                elif 'repository' in tool_name or 'repositories' in tool_name:
                    item_type = "repositories"
                elif 'branch' in tool_name:
                    item_type = "branches"
                else:
                    item_type = "items"
                return f"  Found {count} {item_type}"
            except:
                return "  List retrieved successfully"
        
        else:
            # Generic result summary
            if len(content_str) > 200:
                return f"  Result received ({len(content_str)} chars)\n  Preview: {content_str[:100]}..."
            else:
                return f"  Result: {content_str}"
            
    async def use_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        log_callback: Optional[Callable[[str], None]] = None,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool through appropriate MCP server.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            log_callback: Optional callback for logging
            platform: Optional platform override
            
        Returns:
            Tool execution result
        """
        try:
            # Determine target platform
            target_platform = platform
            if not target_platform:
                # Try to detect from tool name
                target_platform = self._detect_platform_from_tool(tool_name)
            if not target_platform:
                # Try to detect from arguments
                target_platform = self._detect_platform_from_args(tool_args)
            if not target_platform:
                # Use active platform or default
                target_platform = self._active_platform or self.config.default_platform
            
            # Check if target platform is connected
            if target_platform == self.config.PLATFORM_GITHUB and not self._github_connected:
                raise RuntimeError("GitHub MCP server not connected")
            elif target_platform == self.config.PLATFORM_BITBUCKET and not self._bitbucket_connected:
                raise RuntimeError("Bitbucket API not connected")
            
            # Convert tool name and arguments if needed
            actual_tool_name = tool_name
            actual_tool_args = tool_args
            
            if target_platform == self.config.PLATFORM_BITBUCKET:
                # If this is a GitHub tool being used on Bitbucket, convert it
                if not tool_name.startswith('bitbucket_') and 'bitbucket' not in tool_name:
                    actual_tool_name = self._convert_github_to_bitbucket_tool_name(tool_name)
                    actual_tool_args = self._convert_github_to_bitbucket_args(tool_name, tool_args)
            
            # Log tool start with formatted parameters
            if log_callback:
                formatted_args = self._format_tool_args(actual_tool_name, actual_tool_args)
                platform_info = f" ({target_platform.upper()})"
                log_callback(f"▶ Starting tool: {actual_tool_name}{platform_info}\n{formatted_args}")
            
            # Execute tool on appropriate platform
            if target_platform == self.config.PLATFORM_GITHUB:
                result = await self.github_connector.use_tool(
                    tool_name=actual_tool_name, 
                    tool_args=actual_tool_args
                )
                result_content = result.content
            elif target_platform == self.config.PLATFORM_BITBUCKET:
                result = await self.bitbucket_connector.use_tool(
                    tool_name=actual_tool_name, 
                    tool_args=actual_tool_args
                )
                result_content = result.content
                if result.is_error:
                    raise Exception(result_content)
            else:
                raise RuntimeError(f"Unsupported platform: {target_platform}")
            
            # Log successful completion with result summary
            logger.info(f"Tool '{actual_tool_name}' executed successfully on {target_platform}")
            if log_callback:
                result_summary = self._summarize_result(actual_tool_name, result_content)
                log_callback(f"✓ Tool {actual_tool_name} completed:\n{result_summary}")
                
            return {"success": True, "content": result_content, "platform": target_platform}
            
        except Exception as e:
            error_msg = f"Tool '{tool_name}' failed with error: {str(e)}"
            logger.error(error_msg)
            
            if log_callback:
                log_callback(f"✗ Tool {tool_name} failed:\n  Error: {str(e)}")
                
            return {"success": False, "error": str(e), "content": error_msg}
            
    async def handle_tool_use(
        self,
        response: Any,
        messages: List[Dict[str, Any]],
        client: Any,
        message_params: Dict[str, Any],
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Any:
        """
        Handle tool use in a conversation loop.
        
        Args:
            response: Initial response from Claude
            messages: Conversation messages
            client: Anthropic client
            message_params: Parameters for message creation
            log_callback: Optional callback for logging
            
        Returns:
            Final response after tool usage
        """
        while response.stop_reason == "tool_use":
            for content in response.content:
                if content.type != "tool_use":
                    continue
                    
                tool_name = content.name
                tool_args = content.input
                tool_id = content.id
                
                # Execute tool
                result = await self.use_tool(tool_name, tool_args, log_callback)
                
                # Add assistant message with tool use
                message_params["messages"].append({
                    "role": response.role,
                    "content": response.content
                })
                
                # Add user message with tool result
                tool_result_message = {
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result.get("content", "")
                    }]
                }
                message_params["messages"].append(tool_result_message)
                
                # Get next response
                response = client.create_message(**message_params)
                logger.info(f"Received follow-up response after tool use")
                
        return response
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to any MCP server."""
        return self._github_connected or self._bitbucket_connected
    
    @property
    def connected_platforms(self) -> List[str]:
        """Get list of connected platforms."""
        platforms = []
        if self._github_connected:
            platforms.append(self.config.PLATFORM_GITHUB)
        if self._bitbucket_connected:
            platforms.append(self.config.PLATFORM_BITBUCKET)
        return platforms
    
    @property
    def active_platform(self) -> Optional[str]:
        """Get the currently active platform."""
        return self._active_platform
    
    def set_active_platform(self, platform: str) -> bool:
        """
        Set the active platform.
        
        Args:
            platform: Platform to set as active
            
        Returns:
            True if platform was set successfully
        """
        if not self.config.is_platform_supported(platform):
            logger.error(f"Unsupported platform: {platform}")
            return False
        
        platform = platform.lower()
        
        if platform == self.config.PLATFORM_GITHUB and not self._github_connected:
            logger.error("Cannot set GitHub as active platform - not connected")
            return False
        elif platform == self.config.PLATFORM_BITBUCKET and not self._bitbucket_connected:
            logger.error("Cannot set Bitbucket as active platform - not connected")
            return False
        
        self._active_platform = platform
        logger.info(f"Active platform set to: {platform}")
        return True
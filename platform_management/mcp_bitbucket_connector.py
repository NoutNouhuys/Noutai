"""
MCP Bitbucket Connector

Handles connection and communication with Bitbucket MCP server.
Provides tool mapping and conversion for Bitbucket-specific operations.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
import mcp_connector
from anthropic_config import AnthropicConfig

logger = logging.getLogger(__name__)


class MCPBitbucketConnector:
    """Manages MCP server connections specifically for Bitbucket."""
    
    def __init__(self, config: AnthropicConfig):
        """
        Initialize Bitbucket MCP connector.
        
        Args:
            config: AnthropicConfig instance
        """
        self.config = config
        self.connector = mcp_connector.MCPConnector()
        self._connected = False
        self.platform = "bitbucket"
        
    async def connect(self, server_script_path: Optional[str] = None, server_venv_path: Optional[str] = None) -> bool:
        """
        Connect to Bitbucket MCP server.
        
        Args:
            server_script_path: Path to Bitbucket MCP server script
            server_venv_path: Path to virtual environment
            
        Returns:
            True if connection successful
        """
        try:
            script_path = server_script_path or self.config.bitbucket_mcp_server_script
            venv_path = server_venv_path or self.config.bitbucket_mcp_server_venv_path
            
            if not script_path:
                logger.debug("No Bitbucket MCP server script path configured")
                return False
                
            await self.connector.connect_to_server(script_path, venv_path)
            self._connected = True
            logger.info("Successfully connected to Bitbucket MCP server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Bitbucket MCP server: {str(e)}")
            return False
            
    async def disconnect(self) -> None:
        """Disconnect from Bitbucket MCP server."""
        if self._connected:
            try:
                await self.connector.close()
                self._connected = False
                logger.info("Disconnected from Bitbucket MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from Bitbucket MCP server: {str(e)}")
                
    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get available tools from Bitbucket MCP server.
        
        Returns:
            List of tool definitions
        """
        if not self._connected:
            return []
            
        try:
            tools = await self.connector.get_tools()
            
            # Remove duplicates and add platform identifier
            unique_tools = []
            seen = set()
            for tool in tools:
                if tool["name"] not in seen:
                    # Add platform identifier to tool
                    tool["platform"] = self.platform
                    unique_tools.append(tool)
                    seen.add(tool["name"])
                    
            logger.debug(f"Retrieved {len(unique_tools)} unique tools from Bitbucket MCP server")
            return unique_tools
            
        except Exception as e:
            logger.error(f"Failed to get tools from Bitbucket MCP server: {str(e)}")
            return []
    
    def _format_tool_args(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Format tool arguments for readable logging - Bitbucket specific."""
        if tool_name == "get_file_contents":
            workspace = tool_args.get('workspace', 'unknown')
            repo_slug = tool_args.get('repo_slug', 'unknown')
            path = tool_args.get('path', 'unknown')
            branch = tool_args.get('branch', 'main')
            return f"  Repository: {workspace}/{repo_slug}\\n  Path: {path}\\n  Branch: {branch}"
        
        elif tool_name == "create_issue":
            workspace = tool_args.get('workspace', 'unknown')
            repo_slug = tool_args.get('repo_slug', 'unknown')
            title = tool_args.get('title', 'No title')
            priority = tool_args.get('priority', 'medium')
            return f"  Repository: {workspace}/{repo_slug}\\n  Title: {title}\\n  Priority: {priority}"
        
        elif tool_name == "update_issue":
            workspace = tool_args.get('workspace', 'unknown')
            repo_slug = tool_args.get('repo_slug', 'unknown')
            issue_id = tool_args.get('issue_id', 'unknown')
            title = tool_args.get('title', 'No title change')
            state = tool_args.get('state', 'No state change')
            return f"  Repository: {workspace}/{repo_slug}\\n  Issue: #{issue_id}\\n  Title: {title}\\n  State: {state}"
        
        elif tool_name == "create_pull_request":
            workspace = tool_args.get('workspace', 'unknown')
            repo_slug = tool_args.get('repo_slug', 'unknown')
            title = tool_args.get('title', 'No title')
            source_branch = tool_args.get('source_branch', 'unknown')
            destination_branch = tool_args.get('destination_branch', 'unknown')
            return f"  Repository: {workspace}/{repo_slug}\\n  Title: {title}\\n  From: {source_branch} → {destination_branch}"
        
        elif tool_name == "merge_pull_request":
            workspace = tool_args.get('workspace', 'unknown')
            repo_slug = tool_args.get('repo_slug', 'unknown')
            pr_id = tool_args.get('pull_request_id', 'unknown')
            merge_strategy = tool_args.get('merge_strategy', 'merge_commit')
            return f"  Repository: {workspace}/{repo_slug}\\n  Pull Request: #{pr_id}\\n  Strategy: {merge_strategy}"
        
        elif tool_name == "create_or_update_file":
            workspace = tool_args.get('workspace', 'unknown')
            repo_slug = tool_args.get('repo_slug', 'unknown')
            path = tool_args.get('path', 'unknown')
            branch = tool_args.get('branch', 'main')
            content_size = len(str(tool_args.get('content', '')))
            return f"  Repository: {workspace}/{repo_slug}\\n  Path: {path}\\n  Branch: {branch}\\n  Content size: {content_size} chars"
        
        elif tool_name == "list_issues":
            workspace = tool_args.get('workspace', 'unknown')
            repo_slug = tool_args.get('repo_slug', 'unknown')
            state = tool_args.get('state', 'open')
            return f"  Repository: {workspace}/{repo_slug}\\n  State: {state}"
        
        elif tool_name == "search_repositories":
            query = tool_args.get('query', 'No query')
            return f"  Query: {query}\\n  Platform: Bitbucket"
        
        elif tool_name == "create_repository":
            workspace = tool_args.get('workspace', 'unknown')
            name = tool_args.get('name', 'unknown')
            is_private = tool_args.get('is_private', True)
            description = tool_args.get('description', 'No description')
            return f"  Workspace: {workspace}\\n  Name: {name}\\n  Private: {is_private}\\n  Description: {description}"
        
        elif tool_name == "fork_repository":
            workspace = tool_args.get('workspace', 'unknown')
            repo_slug = tool_args.get('repo_slug', 'unknown')
            new_workspace = tool_args.get('new_workspace', 'Personal workspace')
            return f"  Repository: {workspace}/{repo_slug}\\n  Fork to: {new_workspace}"
        
        else:
            # Generic formatting for unknown tools
            formatted_args = []
            for key, value in tool_args.items():
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                formatted_args.append(f"  {key}: {value}")
            return "\\n".join(formatted_args) if formatted_args else "  No parameters"
    
    def _summarize_result(self, tool_name: str, content: Any) -> str:
        """Make a concise summary of the result - Bitbucket specific."""
        if not content:
            return "  No result content"
        
        content_str = str(content)
        
        # Tool-specific result summaries for Bitbucket
        if tool_name == "get_file_contents":
            try:
                if "content" in content_str:
                    content_length = len(content_str)
                    return f"  File retrieved ({content_length/1024:.1f} KB)\\n  Platform: Bitbucket"
                else:
                    return f"  File content retrieved ({len(content_str)} chars)\\n  Platform: Bitbucket"
            except:
                return f"  File content retrieved ({len(content_str)} chars)\\n  Platform: Bitbucket"
        
        elif tool_name in ["create_issue", "update_issue"]:
            if "id" in content_str:
                try:
                    import re
                    match = re.search(r'"id":\\s*(\\d+)', content_str)
                    if match:
                        issue_id = match.group(1)
                        return f"  Issue #{issue_id} processed successfully\\n  Platform: Bitbucket"
                except:
                    pass
            return "  Issue processed successfully\\n  Platform: Bitbucket"
        
        elif tool_name == "create_pull_request":
            if "id" in content_str:
                try:
                    import re
                    match = re.search(r'"id":\\s*(\\d+)', content_str)
                    if match:
                        pr_id = match.group(1)
                        return f"  Pull Request #{pr_id} created\\n  Platform: Bitbucket"
                except:
                    pass
            return "  Pull Request created successfully\\n  Platform: Bitbucket"
        
        elif tool_name == "merge_pull_request":
            if "state" in content_str and "MERGED" in content_str:
                return "  Pull Request merged successfully\\n  Platform: Bitbucket"
            return "  Pull Request merge processed\\n  Platform: Bitbucket"
        
        elif tool_name in ["create_or_update_file"]:
            if "hash" in content_str:
                try:
                    import re
                    match = re.search(r'"hash":\\s*"([a-f0-9]{7})', content_str)
                    if match:
                        hash_val = match.group(1)
                        return f"  File committed (Hash: {hash_val})\\n  Platform: Bitbucket"
                except:
                    pass
            return "  File committed successfully\\n  Platform: Bitbucket"
        
        elif tool_name == "list_issues":
            try:
                import re
                matches = re.findall(r'"id":', content_str)
                count = len(matches)
                return f"  Found {count} issues\\n  Platform: Bitbucket"
            except:
                return "  Issues list retrieved successfully\\n  Platform: Bitbucket"
        
        elif tool_name == "search_repositories":
            try:
                import re
                match = re.search(r'"size":\\s*(\\d+)', content_str)
                if match:
                    total = match.group(1)
                    return f"  Found {total} repositories\\n  Platform: Bitbucket"
            except:
                pass
            return "  Search completed successfully\\n  Platform: Bitbucket"
        
        else:
            # Generic result summary
            if len(content_str) > 200:
                return f"  Result received ({len(content_str)} chars)\\n  Platform: Bitbucket\\n  Preview: {content_str[:100]}..."
            else:
                return f"  Result: {content_str}\\n  Platform: Bitbucket"
            
    async def use_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool through Bitbucket MCP server.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            log_callback: Optional callback for logging
            
        Returns:
            Tool execution result
        """
        try:
            if not self._connected:
                raise RuntimeError("Not connected to Bitbucket MCP server")
            
            # Log tool start with formatted parameters
            if log_callback:
                formatted_args = self._format_tool_args(tool_name, tool_args)
                log_callback(f"▶ Starting Bitbucket tool: {tool_name}\\n{formatted_args}")
                
            result = await self.connector.use_tool(tool_name=tool_name, tool_args=tool_args)
            
            # Log successful completion with result summary
            logger.info(f"Bitbucket tool '{tool_name}' executed successfully")
            if log_callback:
                result_summary = self._summarize_result(tool_name, result.content)
                log_callback(f"✓ Bitbucket tool {tool_name} completed:\\n{result_summary}")
                
            return {"success": True, "content": result.content, "platform": self.platform}
            
        except Exception as e:
            error_msg = f"Bitbucket tool '{tool_name}' failed with error: {str(e)}"
            logger.error(error_msg)
            
            if log_callback:
                log_callback(f"✗ Bitbucket tool {tool_name} failed:\\n  Error: {str(e)}")
                
            return {"success": False, "error": str(e), "content": error_msg, "platform": self.platform}
            
    @property
    def is_connected(self) -> bool:
        """Check if connected to Bitbucket MCP server."""
        return self._connected
        
    @property
    def platform_name(self) -> str:
        """Get platform name."""
        return self.platform
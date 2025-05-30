"""
MCP (Model Context Protocol) integration module.
Handles communication with MCP servers for tool usage.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
import mcp_connector
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
        self.connector = mcp_connector.MCPConnector()
        self._connected = False
        
    async def connect(self, server_script_path: Optional[str] = None, server_venv_path: Optional[str] = None) -> bool:
        """
        Connect to MCP server.
        
        Args:
            server_script_path: Path to server script
            server_venv_path: Path to virtual environment
            
        Returns:
            True if connection successful
        """
        try:
            script_path = server_script_path or self.config.mcp_server_script
            venv_path = server_venv_path or self.config.mcp_server_venv_path
            
            if not script_path:
                logger.debug("No MCP server script path configured")
                return False
                
            await self.connector.connect_to_server(script_path, venv_path)
            self._connected = True
            logger.info("Successfully connected to MCP server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            return False
            
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self._connected:
            try:
                await self.connector.close()
                self._connected = False
                logger.info("Disconnected from MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server: {str(e)}")
                
    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get available tools from MCP server.
        
        Returns:
            List of tool definitions
        """
        if not self._connected:
            return []
            
        try:
            tools = await self.connector.get_tools()
            
            # Remove duplicates
            unique_tools = []
            seen = set()
            for tool in tools:
                if tool["name"] not in seen:
                    unique_tools.append(tool)
                    seen.add(tool["name"])
                    
            logger.debug(f"Retrieved {len(unique_tools)} unique tools from MCP server")
            return unique_tools
            
        except Exception as e:
            logger.error(f"Failed to get tools from MCP server: {str(e)}")
            return []
    
    def _format_tool_args(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Format tool arguments for readable logging."""
        if tool_name == "get_file_contents":
            repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            path = tool_args.get('path', 'unknown')
            ref = tool_args.get('ref', 'main')
            return f"  Repository: {repo_info}\n  Path: {path}\n  Branch/Ref: {ref}"
        
        elif tool_name == "create_issue":
            repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            title = tool_args.get('title', 'No title')
            labels = tool_args.get('labels', [])
            return f"  Repository: {repo_info}\n  Title: {title}\n  Labels: {', '.join(labels) if labels else 'None'}"
        
        elif tool_name == "update_issue":
            repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            issue_num = tool_args.get('issue_number', 'unknown')
            title = tool_args.get('title', 'No title change')
            state = tool_args.get('state', 'No state change')
            return f"  Repository: {repo_info}\n  Issue: #{issue_num}\n  Title: {title}\n  State: {state}"
        
        elif tool_name == "create_pull_request":
            repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            title = tool_args.get('title', 'No title')
            head = tool_args.get('head', 'unknown')
            base = tool_args.get('base', 'unknown')
            return f"  Repository: {repo_info}\n  Title: {title}\n  From: {head} → {base}"
        
        elif tool_name == "merge_pull_request":
            repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            pr_num = tool_args.get('pull_number', 'unknown')
            method = tool_args.get('merge_method', 'merge')
            return f"  Repository: {repo_info}\n  Pull Request: #{pr_num}\n  Method: {method}"
        
        elif tool_name == "create_or_update_file":
            repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            path = tool_args.get('path', 'unknown')
            branch = tool_args.get('branch', 'main')
            content_size = len(str(tool_args.get('content', '')))
            return f"  Repository: {repo_info}\n  Path: {path}\n  Branch: {branch}\n  Content size: {content_size} chars"
        
        elif tool_name == "push_files":
            repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            branch = tool_args.get('branch', 'unknown')
            files = tool_args.get('files', [])
            file_count = len(files)
            return f"  Repository: {repo_info}\n  Branch: {branch}\n  Files: {file_count} files"
        
        elif tool_name == "list_issues":
            repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            state = tool_args.get('state', 'open')
            labels = tool_args.get('labels', [])
            return f"  Repository: {repo_info}\n  State: {state}\n  Labels: {', '.join(labels) if labels else 'All'}"
        
        elif tool_name == "search_issues":
            query = tool_args.get('query', 'No query')
            per_page = tool_args.get('per_page', 30)
            return f"  Query: {query}\n  Per page: {per_page}"
        
        elif tool_name == "search_repositories":
            query = tool_args.get('query', 'No query')
            sort = tool_args.get('sort', 'best match')
            return f"  Query: {query}\n  Sort: {sort}"
        
        elif tool_name == "create_repository":
            name = tool_args.get('name', 'unknown')
            private = tool_args.get('private', True)
            description = tool_args.get('description', 'No description')
            return f"  Name: {name}\n  Private: {private}\n  Description: {description}"
        
        elif tool_name == "fork_repository":
            repo_info = f"{tool_args.get('owner', 'unknown')}/{tool_args.get('repo', 'unknown')}"
            org = tool_args.get('organization', 'Personal account')
            return f"  Repository: {repo_info}\n  Fork to: {org}"
        
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
        if tool_name == "get_file_contents":
            try:
                # Try to extract useful info from file content result
                if "type" in content_str and "content" in content_str:
                    # Estimate file size
                    content_length = len(content_str)
                    file_type = "text" if "text" in content_str else "binary"
                    return f"  File retrieved ({content_length/1024:.1f} KB)\n  Type: {file_type}"
                else:
                    return f"  File content retrieved ({len(content_str)} chars)"
            except:
                return f"  File content retrieved ({len(content_str)} chars)"
        
        elif tool_name in ["create_issue", "update_issue"]:
            if "number" in content_str:
                try:
                    # Extract issue number if possible
                    import re
                    match = re.search(r'"number":\s*(\d+)', content_str)
                    if match:
                        issue_num = match.group(1)
                        return f"  Issue #{issue_num} processed successfully"
                except:
                    pass
            return "  Issue processed successfully"
        
        elif tool_name == "create_pull_request":
            if "number" in content_str:
                try:
                    import re
                    match = re.search(r'"number":\s*(\d+)', content_str)
                    if match:
                        pr_num = match.group(1)
                        return f"  Pull Request #{pr_num} created"
                except:
                    pass
            return "  Pull Request created successfully"
        
        elif tool_name == "merge_pull_request":
            if "merged" in content_str:
                return "  Pull Request merged successfully"
            return "  Pull Request merge processed"
        
        elif tool_name in ["create_or_update_file", "push_files"]:
            if "commit" in content_str:
                try:
                    import re
                    match = re.search(r'"sha":\s*"([a-f0-9]{7})', content_str)
                    if match:
                        sha = match.group(1)
                        return f"  Files committed (SHA: {sha})"
                except:
                    pass
            return "  Files committed successfully"
        
        elif tool_name in ["list_issues", "list_pull_requests"]:
            # Count items in list result
            try:
                import re
                # Count occurrences of "number": which indicates items
                matches = re.findall(r'"number":', content_str)
                count = len(matches)
                item_type = "issues" if "issue" in tool_name else "pull requests"
                return f"  Found {count} {item_type}"
            except:
                return "  List retrieved successfully"
        
        elif tool_name in ["search_issues", "search_repositories"]:
            try:
                import re
                # Look for total_count in search results
                match = re.search(r'"total_count":\s*(\d+)', content_str)
                if match:
                    total = match.group(1)
                    item_type = "issues" if "issue" in tool_name else "repositories"
                    return f"  Found {total} {item_type}"
            except:
                pass
            return "  Search completed successfully"
        
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
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool through MCP server.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            log_callback: Optional callback for logging
            
        Returns:
            Tool execution result
        """
        try:
            if not self._connected:
                raise RuntimeError("Not connected to MCP server")
            
            # Log tool start with formatted parameters
            if log_callback:
                formatted_args = self._format_tool_args(tool_name, tool_args)
                log_callback(f"▶ Starting tool: {tool_name}\n{formatted_args}")
                
            result = await self.connector.use_tool(tool_name=tool_name, tool_args=tool_args)
            
            # Log successful completion with result summary
            logger.info(f"Tool '{tool_name}' executed successfully")
            if log_callback:
                result_summary = self._summarize_result(tool_name, result.content)
                log_callback(f"✓ Tool {tool_name} completed:\n{result_summary}")
                
            return {"success": True, "content": result.content}
            
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
                response = response = client.create_message(**message_params)
                logger.info(f"Received follow-up response after tool use")
                
        return response
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        return self._connected
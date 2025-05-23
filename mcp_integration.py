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
                
            result = await self.connector.use_tool(tool_name=tool_name, tool_args=tool_args)
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            if log_callback:
                log_callback(f"Tool {tool_name} executed successfully")
                
            return {"success": True, "content": result.content}
            
        except Exception as e:
            error_msg = f"Tool '{tool_name}' failed with error: {str(e)}"
            logger.error(error_msg)
            
            if log_callback:
                log_callback(error_msg)
                
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
                response = client.messages.create(**message_params)
                logger.info(f"Received follow-up response after tool use")
                
                if log_callback:
                    log_callback(f"Result from {tool_name}: {result.get('content', '')}")
                    
        return response
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        return self._connected
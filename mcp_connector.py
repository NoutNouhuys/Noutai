from contextlib import AsyncExitStack
import os
import logging
from typing import Optional, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys

# TODO Adjust to use multiple servers

logger = logging.getLogger(__name__)

class MCPConnector:
    """
    Class to manage the connection to MCP servers.
    """
    def __init__(self):
        # Initialize session and client objects
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(
        self,
        server_script_path: str,
        python_executable_path: Optional[str] = None # New parameter
    ) -> None:
        """Connect to an MCP server, optionally using a specific Python executable.

        Args:
            server_script_path: Path to the server script (.py or .js).
            python_executable_path: Optional full path to the Python executable
                                    (e.g., from a specific venv) to run .py scripts.
                                    If None, uses the default 'python'.
        """
        # Check if the server script path is valid
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = ""
        if is_python:
            # Construct the path to the python executable within that venv
            # This depends on your OS
            if sys.platform == "win32":
                python_in_venv = os.path.join(python_executable_path, "Scripts", "python.exe")
            else: # Linux, macOS, etc.
                python_in_venv = os.path.join(python_executable_path, "bin", "python")
                # TODO test mac

            # Use the provided Python executable if given, otherwise default to 'python'
            command = python_in_venv if python_executable_path else "python"
            # Optional: Add a check to ensure the provided path exists
            if python_executable_path and not os.path.isfile(python_in_venv):
                 raise FileNotFoundError(f"Specified Python executable not found: {python_in_venv}")
        elif is_js:
            command = "node" # Assuming node is in PATH, or provide full path if needed

        # Start the server using the command and script path
        logger.info(f"Starting server using command: '{command}' with script: '{server_script_path}'")
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None # You could potentially manipulate PATH here too, but direct executable path is cleaner
        )

        # connect to the server
        logger.info(f"Connecting to server with parameters: {server_params}")
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools in logs
        response = await self.session.list_tools()
        logger.debug(f"\nConnected to server with tools: {[tool.name for tool in response.tools]}")

    
    async def get_tools(self):
        """Get the list of available tools from the server."""
        self.fail_if_no_session()
        
        response = await self.session.list_tools()

        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        return available_tools
    

    async def use_tool(self, tool_name, tool_args) -> Any:
        """Use a specific tool with the given arguments.

        Args:
            tool_name: Name of the tool to use.
            tool_args: Arguments to pass to the tool.

        Returns:
            The response from the tool.
        """
        self.fail_if_no_session()
        
        # Call the tool with the provided arguments
        logger.debug(f"Calling tool '{tool_name}' with arguments: {tool_args}")
        result = await self.session.call_tool(tool_name, tool_args)

        logger.debug(f"Tool '{tool_name}' response: {result}")     

        # check for error and raise an exception if needed
        if result.isError:
            error_message = f"Error executing tool {tool_name}: {result.content}"
            logger.error(error_message)
            raise Exception(error_message)

        return result
    

    def fail_if_no_session(self):
        """Check if the session is initialized and raise an error if not."""
        if not self.session:
            raise RuntimeError("Session not initialized. Please connect to a server first.")



    async def close(self):
         """Cleanly close the connection and exit the stack."""
         await self.exit_stack.aclose()
         print("Connection closed.")

    


import os
import time
import json
import uuid
import logging
import requests
import subprocess
import asyncio
from typing import Dict, List, Optional, Tuple, Union, Any
import anthropic
from flask import current_app
from repositories.conversation_repository import ConversationRepository
from config import BaseConfig
import mcp_connector

# Setup logger
logger = logging.getLogger(__name__)

class AnthropicAPI:
    """
    Module for interacting with the Anthropic Claude API.
    This class handles communication with Claude models and manages conversations.
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Anthropic API client.
        
        Args:
            api_key: Optional API key. If not provided, it will be retrieved from config.
            config: Optional configuration dictionary. If not provided, it will use Flask app's config.
        """
        self.config = config or {}
        
        # Get API key from parameters, config, or environment
        self.api_key = api_key or self.config.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            logger.error("Anthropic API key is not provided")
            raise ValueError("Anthropic API key is required but not provided")
        
        # Anthropic client will be lazily initialized
        self.client = None
        
        # In-memory store for conversations (temporary until database)
        self.conversations = {}
        
        # Configure default model and parameters
        self._configure_defaults()
    
    def _configure_defaults(self):
        """Configure default model and parameters from app config"""
        # Set default model
        self.default_model = self.config.get('ANTHROPIC_DEFAULT_MODEL') or 'claude-3-haiku-20240307'
        
        # Set global maximum token limit (used as fallback or override)
        self.max_tokens = self.config.get('ANTHROPIC_MAX_TOKENS') or 4000

        # TTL for Anthropic prompt caching
        self.cache_ttl = self.config.get('ANTHROPIC_CACHE_TTL', '5m')
        
        # Set default system prompt
        self.system_prompt = self.config.get('ANTHROPIC_SYSTEM_PROMPT') or None
        
        # Set default werkwijze
        self.werkwijze = self.config.get('ANTHROPIC_WERKWIJZE') or None

        logger.debug(
            f"AnthropicAPI configured with model: {self.default_model}, "
            f"global max_tokens: {self.max_tokens}, cache_ttl: {self.cache_ttl}"
        )

    def _apply_cache_control(self, messages: List[Dict[str, Any]]) -> None:
        """Apply prompt caching if supported by the API.

        The Anthropic API no longer accepts the ``cache_control`` field inside
        message objects.  To avoid request errors we skip setting this flag.
        The method remains for future compatibility so existing calls do not
        fail if caching is reintroduced later.
        """
        return

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available Claude models.
        
        Returns:
            List of available models with name, description, context length and max output tokens.
        """
        # Define available models for use in the UI
        # This is hardcoded for now, but could be fetched from the API in the future
        return [
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "description": "Most powerful for complex tasks",
                "context_length": 200000,
                "max_tokens": 20480,
            },
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "description": "Balance of intelligence and speed",
                "context_length": 200000,
                "max_tokens": 8192,
            },
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "description": "Fastest model for simpler tasks",
                "context_length": 200000,
                "max_tokens": 4096,
            },
            {
                "id": "claude-3-7-sonnet-20250219",
                "name":"Claude 3.7 Sonnet",
                "description": "Current most intelligent model",
                "context_length": 200000,
                "max_tokens": 20480,
            }
        ]
    
    def get_model_max_tokens(self, model_id: str) -> int:
        """
        Get the maximum output tokens for a specific model.
        
        Args:
            model_id: The ID of the model to get max tokens for
            
        Returns:
            Maximum output tokens for the specified model or the default max_tokens
        """
        for model in self.get_available_models():
            if model["id"] == model_id:
                return model.get("max_tokens", self.max_tokens)
        
        # If model not found, return the default max_tokens
        logger.warning(f"Model {model_id} not found in available models, using default max_tokens: {self.max_tokens}")
        return self.max_tokens
    
    def create_conversation(self) -> str:
        """
        Create a new conversation.
        
        Returns:
            Unique conversation ID
        """
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = []
        return conversation_id
    
    def get_conversation(self, conversation_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Retrieve the conversation history.
        
        Args:
            conversation_id: The ID of the conversation to retrieve
            
        Returns:
            List of message objects in the conversation
        
        Raises:
            ValueError: If the conversation ID doesn't exist
        """
        # Convert to string if it's an integer
        conversation_id_str = str(conversation_id)
        
        if conversation_id_str not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found in memory store")
            raise ValueError(f"Conversation {conversation_id} not found")
        
        return self.conversations[conversation_id_str]
    
    def add_to_conversation(self, conversation_id: Union[str, int], user_message: str, system_message: str) -> None:
        """
        Add a prompt and response to a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            user_message: The user's prompt to add
            system_message: The system's response to add
            
        Raises:
            ValueError: If the conversation ID doesn't exist
        """
        # Convert to string if it's an integer
        conversation_id_str = str(conversation_id)
        
        if conversation_id_str not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
            
        timestamp = time.time()
        
        # Add user message
        self.conversations[conversation_id_str].append({
            "role": "user",
            "content": user_message,
            "timestamp": timestamp
        })
        
        # Add system message
        self.conversations[conversation_id_str].append({
            "role": "assistant",
            "content": system_message,
            "timestamp": timestamp + 0.001  # Ensure it comes after user message
        })

    async def _send_prompt_async(
        self,
        message_params: Dict[str, Any],
        server_script_path: Optional[str],
        server_venv_path: Optional[str],
        include_logs: bool,
        emit_log: callable,
    ) -> str:
        """Internal coroutine to send the prompt and handle tool use.

        Args:
            message_params: Parameters for the Anthropic API call.
            server_script_path: Optional path to an MCP server script.
            server_venv_path: Optional path to the server's virtual environment.
            include_logs: Whether to emit log messages.
            emit_log: Callback for log emission.

        Returns:
            The text content from the model's response.
        """
        mcp_connector_instance = mcp_connector.MCPConnector()
        tools: List[Dict[str, Any]] = []
        connection_opened = False

        try:
            if server_script_path:
                await mcp_connector_instance.connect_to_server(
                    server_script_path, server_venv_path
                )
                connection_opened = True
                if include_logs:
                    emit_log("Verbinding met MCP-server opgezet")
                tools = await mcp_connector_instance.get_tools()

            tools.append(
                {
                    "name": "get_werkwijze",
                    "description": (
                        "Read the werkwijze for the project. "
                        "This is important as it gives the steps to take for development."
                    ),
                    "input_schema": {"type": "object", "properties": {}, "required": []},
                }
            )

            unique_tools = []
            seen = set()
            for t in tools:
                if t["name"] not in seen:
                    unique_tools.append(t)
                    seen.add(t["name"])
            tools = unique_tools

            message_params["tools"] = tools

            if self.client is None:
                self.client = anthropic.Anthropic(api_key=self.api_key)

            response = self.client.messages.create(**message_params)
            print(f"Ontvangen message: {response.content}")
            if include_logs:
                emit_log("Prompt verzonden naar Claude")

            while response.stop_reason == "tool_use":
                for c in response.content:
                    if c.type != "tool_use":
                        continue
                    tool_name = c.name
                    tool_args = c.input
                    tool_id = c.id

                    try:
                        if tool_name == "get_werkwijze":
                            tool_result = self.werkwijze or "Werkwijze not found"
                        else:
                            if not mcp_connector_instance.session:
                                await mcp_connector_instance.connect_to_server(
                                    server_script_path, server_venv_path
                                )
                                connection_opened = True
                                if include_logs:
                                    emit_log("Verbinding met MCP-server opgezet")
                            result = await mcp_connector_instance.use_tool(
                                tool_name=tool_name, tool_args=tool_args
                            )
                            tool_result = result.content

                        logger.info(
                            f"Tool '{tool_name}' executed successfully with result: {tool_result}"
                        )
                        if include_logs:
                            emit_log(f"Tool {tool_name} uitgevoerd")
                    except Exception as tool_error:
                        logger.error(
                            f"Error during tool execution '{tool_name}': {str(tool_error)}"
                        )
                        tool_result = (
                            f"Tool '{tool_name}' failed with error: {str(tool_error)}"
                        )
                        if include_logs:
                            emit_log(tool_result)

                    message_params["messages"].append(
                        {"role": response.role, "content": response.content}
                    )

                    tool_result_payload = {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": tool_result,
                    }
                    next_messages = message_params["messages"].copy()
                    tool_result_message = {
                        "role": "user",
                        "content": [tool_result_payload],
                    }

                    next_messages.append(tool_result_message)
                    message_params["messages"] = next_messages
                    response = self.client.messages.create(**message_params)
                    logger.info(f"Ontvangen message: {response.content}")
                    if include_logs:
                        emit_log(f"Resultaat van {tool_name}: {tool_result}")

            response_text = response.content[0].text
            if include_logs:
                emit_log("Antwoord van Claude ontvangen")

            return response_text
        finally:
            if connection_opened:
                try:
                    await mcp_connector_instance.close()
                except Exception as close_error:
                    logger.error(f"Failed to close MCP connection: {close_error}")
    
    def send_prompt(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        conversation_id: Optional[Union[str, int]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        include_logs: bool = True,
        log_callback: Optional[callable] = None,
        repo_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a prompt to Claude and return the response.

        Args:
            prompt: User prompt to send.
            model_id: Optional model identifier.
            conversation_id: Conversation ID to continue.
            system_prompt: Optional system prompt override.
            max_tokens: Maximum output tokens.
            include_logs: Whether to capture log messages.
            log_callback: Optional callback for log messages.
            repo_path: Path to a repository (no longer used for werkwijze.txt loading).

        Returns:
            Dictionary with response data and metadata.
        """

        model_id = model_id or self.default_model
        system_prompt = system_prompt or self.system_prompt

        if max_tokens is None:
            max_tokens = self.get_model_max_tokens(model_id)
            logger.debug(f"Using model-specific max_tokens: {max_tokens} for model: {model_id}")

        logs: List[str] = []

        def emit_log(message: str) -> None:
            if include_logs:
                logs.append(message)
            if log_callback:
                try:
                    log_callback(message)
                except Exception as callback_error:
                    logger.error(f"Log callback failed: {callback_error}")

        conversation_id_str = str(conversation_id) if conversation_id is not None else None

        loop = ensure_event_loop()

        messages: List[Dict[str, Any]] = []

        if conversation_id_str:
            if conversation_id_str in self.conversations:
                for msg in self.conversations[conversation_id_str]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            else:
                try:
                    if isinstance(conversation_id, int):
                        logger.info(f"Loading conversation {conversation_id} from database")
                        db_messages = ConversationRepository.get_messages(conversation_id)
                        self.conversations[conversation_id_str] = []
                        for msg in db_messages:
                            api_msg = {"role": msg.role, "content": msg.content}
                            messages.append(api_msg)
                            self.conversations[conversation_id_str].append(
                                {
                                    "role": msg.role,
                                    "content": msg.content,
                                    "timestamp": msg.created_at.timestamp(),
                                }
                            )
                except Exception as db_error:
                    logger.error(f"Failed to load conversation from database: {str(db_error)}")

        # Combine configured werkwijze with any provided system prompt
        if self.werkwijze:
            if system_prompt:
                system_prompt = f"{system_prompt}\n\n{self.werkwijze}"
            else:
                system_prompt = self.werkwijze

        messages.append({"role": "user", "content": prompt})
        self._apply_cache_control(messages)

        message_params = {"model": model_id, "messages": messages, "max_tokens": max_tokens}
        if system_prompt:
            message_params["system"] = system_prompt

        server_script_path = os.environ.get("MCP_SERVER_SCRIPT")
        server_venv_path = os.environ.get("MCP_SERVER_VENV_PATH")

        try:
            response_text = loop.run_until_complete(
                self._send_prompt_async(
                    message_params,
                    server_script_path,
                    server_venv_path,
                    include_logs,
                    emit_log,
                )
            )

            if not conversation_id_str:
                conversation_id_str = self.create_conversation()

            self.add_to_conversation(conversation_id_str, prompt, response_text)

            logger.info(
                f"Successfully received response from Anthropic API, conversation: {conversation_id_str}"
            )

            return {
                "conversation_id": conversation_id or conversation_id_str,
                "message": response_text,
                "model": model_id,
                "success": True,
                "logs": logs if include_logs else [],
            }

        except Exception as e:
            logger.error(f"Error in Anthropic API call: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "conversation_id": conversation_id,
                "logs": logs if include_logs else [],
            }


def get_anthropic_api():
    """
    Factory function to create an AnthropicAPI instance with the current app's config.
    Used for integration with Flask application context.
    
    Returns:
        Configured AnthropicAPI instance
    """
    try:
        config = current_app.config
    except RuntimeError:
        # Flask app context not available, use environment variables
        config = BaseConfig.__dict__
    
    return AnthropicAPI(config=config)


# Create a global instance that can be imported by other modules
# This will be lazily initialized when first accessed
_api_instance = None

def get_api_instance():
    """
    Get or create the global AnthropicAPI instance.
    
    Returns:
        Global AnthropicAPI instance
    """
    global _api_instance
    if _api_instance is None:
        _api_instance = get_anthropic_api()
    return _api_instance

# For backwards compatibility
anthropic_api = get_api_instance()


def ensure_event_loop():
    """
    Checks if an asyncio event loop is currently running.  If not,
    it creates a new one and sets it as the default.

    Returns:
        asyncio.AbstractEventLoop: The current or newly created event loop.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

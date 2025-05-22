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
from cache_manager import (
    write_to_cache,
    read_from_cache,
    is_cache_valid,
    clear_cache,
)

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

        # Load important repository files into memory cache
        self._load_file_cache()
    
    def _configure_defaults(self):
        """Configure default model and parameters from app config"""
        # Set default model
        self.default_model = self.config.get('ANTHROPIC_DEFAULT_MODEL') or 'claude-3-haiku-20240307'
        
        # Set global maximum token limit (used as fallback or override)
        self.max_tokens = self.config.get('ANTHROPIC_MAX_TOKENS') or 4000
        
        # Set default system prompt
        self.system_prompt = self.config.get('ANTHROPIC_SYSTEM_PROMPT') or None

        logger.debug(f"AnthropicAPI configured with model: {self.default_model}, global max_tokens: {self.max_tokens}")

    def _load_file_cache(self) -> None:
        """Load important repository files into an in-memory cache."""
        base_path = os.path.dirname(__file__)
        files = {
            "werkwijze": os.path.join(base_path, "werkwijze", "werkwijze.txt"),
            "system_prompt": os.path.join(base_path, "system_prompt.txt"),
            "project_structure": os.path.join(base_path, "project_structure.md"),
        }

        for key, path in files.items():
            try:
                with open(path, "r", encoding="utf-8") as file:
                    write_to_cache(key, file.read())
            except FileNotFoundError:
                logger.warning(f"File {path} not found for cache key '{key}'")
                write_to_cache(key, None)

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
                "max_tokens": 4096,
            },
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "description": "Balance of intelligence and speed",
                "context_length": 200000,
                "max_tokens": 4096,
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
                "max_tokens": 4096,
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
    
    def send_prompt(self, prompt: str, model_id: Optional[str] = None,
                conversation_id: Optional[Union[str, int]] = None,
                system_prompt: Optional[str] = None,
                max_tokens: Optional[int] = None,
                include_logs: bool = True,
                log_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Send a prompt to Claude and get a response, optionally including context from MCP servers.

        Args:
            prompt: The user's prompt text
            model_id: The Claude model to use (defaults to configured default)
            conversation_id: Optional conversation ID to add to existing conversation
            system_prompt: Optional system prompt to control Claude's behavior
            max_tokens: Optional maximum number of tokens in the response
            include_logs: Whether to include logs in the response
            log_callback: Optional callback function for log messages

        Returns:
            Dictionary with response text and metadata
        """
        model_id = model_id or self.default_model
        system_prompt = system_prompt or self.system_prompt
        
        # Get model-specific max_tokens if not explicitly provided
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

        # Convert conversation_id to string if it's an integer
        conversation_id_str = str(conversation_id) if conversation_id is not None else None

        # Retrieve context from MCP servers
        server_script_path = os.environ.get('MCP_SERVER_SCRIPT')
        server_venv_path = os.environ.get('MCP_SERVER_VENV_PATH')
        loop = ensure_event_loop()
        mcp_connector_instance = mcp_connector.MCPConnector()
        tools = []
        tools_cache_key = "mcp_tools"
        connection_opened = False
        if server_script_path:
            if is_cache_valid(tools_cache_key):
                tools = read_from_cache(tools_cache_key) or []
            else:
                loop.run_until_complete(
                    mcp_connector_instance.connect_to_server(server_script_path, server_venv_path)
                )
                connection_opened = True
                if include_logs:
                    emit_log("Verbinding met MCP-server opgezet")
                tools = loop.run_until_complete(mcp_connector_instance.get_tools())
                write_to_cache(
                    tools_cache_key,
                    tools,
                    expiry=self.config.get("CACHE_DEFAULT_EXPIRATION", BaseConfig.CACHE_DEFAULT_EXPIRATION),
                )
        # add read werkwijze tool
        tools.append({
            "name": "get_werkwijze",
            "description": "Read the werkwijze for the project. This is important as it gives the steps to take for development.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        })

        # ensure tools have unique names
        unique_tools = []
        seen = set()
        for t in tools:
            if t["name"] not in seen:
                unique_tools.append(t)
                seen.add(t["name"])
        tools = unique_tools

        # Initialize message list for API call
        messages = []

        # If we have a conversation ID, try to load messages from memory or database
        if conversation_id_str:
            # First check if we have it in memory
            if conversation_id_str in self.conversations:
                for msg in self.conversations[conversation_id_str]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            else:
                # Try to load from database and populate memory cache
                try:
                    if isinstance(conversation_id, int):
                        logger.info(f"Loading conversation {conversation_id} from database")
                        db_messages = ConversationRepository.get_messages(conversation_id)

                        # Initialize the in-memory conversation
                        self.conversations[conversation_id_str] = []

                        for msg in db_messages:
                            api_msg = {
                                "role": msg.role,
                                "content": msg.content
                            }
                            messages.append(api_msg)

                            # Also add to in-memory cache
                            self.conversations[conversation_id_str].append({
                                "role": msg.role,
                                "content": msg.content,
                                "timestamp": msg.created_at.timestamp()
                            })
                except Exception as db_error:
                    logger.error(f"Failed to load conversation from database: {str(db_error)}")

        # Add the new user message
        messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            logger.debug(f"Sending prompt to Claude using model: {model_id} with max_tokens: {max_tokens}")

            if self.client is None:
                self.client = anthropic.Anthropic(api_key=self.api_key)

            message_params = {
                "model": model_id,
                "messages": messages,
                "max_tokens": max_tokens,
                "tools": tools,
            }

            # Add system prompt if provided
            if system_prompt:
                message_params["system"] = system_prompt

            # Call the Anthropic API
            response = self.client.messages.create(**message_params)
            print(f"Ontvangen message: {response.content}")
            if include_logs:
                emit_log("Prompt verzonden naar Claude")

            tool_results = []
            tool_use_id_map = {}  # Track tool_use_id to correctly link with tool_result
            while response.stop_reason == "tool_use":
                for c in response.content:
                    if c.type == "tool_use":
                        tool_name = c.name
                        tool_args = c.input
                        tool_id = c.id
                    
                    # TODO try except error
                        try:
                            if tool_name == "get_werkwijze":
                                if not is_cache_valid("werkwijze"):
                                    self._load_file_cache()
                                tool_result = read_from_cache("werkwijze") or ""
                            else:
                                if not mcp_connector_instance.session:
                                    loop.run_until_complete(
                                        mcp_connector_instance.connect_to_server(server_script_path, server_venv_path)
                                    )
                                    connection_opened = True
                                    if include_logs:
                                        emit_log("Verbinding met MCP-server opgezet")
                                result = loop.run_until_complete(
                                    mcp_connector_instance.use_tool(tool_name=tool_name, tool_args=tool_args)
                                )
                                tool_result = result.content

                            logger.info(
                                f"Tool '{tool_name}' executed successfully with result: {tool_result} (type: {type(tool_result)})"
                            )
                            if include_logs:
                                emit_log(f"Tool {tool_name} uitgevoerd")
                        except Exception as tool_error:
                            logger.error(f"Error during tool execution '{tool_name}': {str(tool_error)}")
                            tool_result = f"Tool '{tool_name}' failed with error: {str(tool_error)}"
                            if include_logs:
                                emit_log(tool_result)

                        #print(f"DEBUG: tool_result: {tool_result}")

                        message_params["messages"].append({
                            "role": response.role,
                            "content": response.content
                        })

                        # Store the result and associate it with the tool_use_id
                        tool_results.append(tool_result)
                        tool_use_id_map[tool_id] = tool_result  # Store the result with tool_use_id


                        # Update message history with tool result
                        tool_result_payload = {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": tool_result,
                        }
                        next_messages = message_params["messages"].copy()
                        tool_result_message = {
                            "role": "user",  # Results are sent back in the 'user' role
                            "content": [tool_result_payload]
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

            # Create a new conversation if needed
            if not conversation_id_str:
                conversation_id_str = self.create_conversation()

            # Add to conversation history in memory
            self.add_to_conversation(conversation_id_str, prompt, response_text)

            logger.info(f"Successfully received response from Anthropic API, conversation: {conversation_id_str}")

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
        finally:
            if connection_opened:
                try:
                    loop.run_until_complete(mcp_connector_instance.close())
                except Exception as close_error:
                    logger.error(f"Failed to close MCP connection: {close_error}")


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
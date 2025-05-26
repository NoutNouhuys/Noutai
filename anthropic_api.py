import os
import time
import json
import uuid
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union, Any
from flask import current_app

from anthropic_config import AnthropicConfig
from anthropic_client import AnthropicClient
from conversation_manager import ConversationManager
from mcp_integration import MCPIntegration
from repositories.conversation_repository import ConversationRepository

# Setup logger
logger = logging.getLogger(__name__)


class AnthropicAPI:
    """
    High-level API for interacting with Anthropic Claude models.
    Coordinates between client, conversation management, and MCP integration.
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Anthropic API.
        
        Args:
            api_key: Optional API key override
            config: Optional configuration dictionary
        """
        # Initialize configuration
        self.anthropic_config = AnthropicConfig(api_key=api_key, config_dict=config)
        
        # Initialize components
        self.client = AnthropicClient(self.anthropic_config)
        self.conversation_manager = ConversationManager()
        # Pass conversation manager to MCP integration for caching
        self.mcp_integration = MCPIntegration(self.anthropic_config, self.conversation_manager)
        
        # For backwards compatibility
        self.api_key = self.anthropic_config.api_key
        self.default_model = self.anthropic_config.default_model
        self.max_tokens = self.anthropic_config.max_tokens
        self.cache_ttl = self.anthropic_config.cache_ttl
        self.system_prompt = self.anthropic_config.system_prompt
        self.werkwijze = self.anthropic_config.werkwijze
        
        logger.debug(f"AnthropicAPI initialized with model: {self.default_model}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available Claude models.
        
        Returns:
            List of available models with metadata
        """
        return self.client.get_available_models()
    
    def get_model_max_tokens(self, model_id: str) -> int:
        """
        Get the maximum output tokens for a specific model.
        
        Args:
            model_id: The ID of the model
            
        Returns:
            Maximum output tokens for the model
        """
        return self.client.get_model_max_tokens(model_id)
    
    def create_conversation(self) -> str:
        """
        Create a new conversation.
        
        Returns:
            Unique conversation ID
        """
        return self.conversation_manager.create_conversation()
    
    def get_conversation(self, conversation_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Retrieve the conversation history.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            List of message objects in the conversation
        """
        messages = self.conversation_manager.get_messages(conversation_id)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]
    
    def add_to_conversation(self, conversation_id: Union[str, int], user_message: str, system_message: str) -> None:
        """
        Add a prompt and response to a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            user_message: The user's prompt
            system_message: The system's response
        """
        self.conversation_manager.add_exchange(conversation_id, user_message, system_message)
    
    async def _send_prompt_async(
        self,
        messages: List[Dict[str, Any]],
        model_id: str,
        max_tokens: int,
        system_prompt: Optional[str],
        emit_log: callable,
        include_logs: bool,
        conversation_id: Optional[Union[str, int]] = None
    ) -> str:
        """
        Internal async method to send prompt and handle tool usage.
        
        Args:
            messages: Conversation messages
            model_id: Model to use
            max_tokens: Maximum output tokens
            system_prompt: System prompt
            emit_log: Logging callback
            include_logs: Whether to emit logs
            conversation_id: Optional conversation ID for context caching
            
        Returns:
            Response text from the model
        """
        # Connect to MCP server if configured
        tools = []
        if self.anthropic_config.mcp_server_script:
            connected = await self.mcp_integration.connect()
            if connected:
                if include_logs:
                    emit_log("Verbinding met MCP-server opgezet")
                tools = await self.mcp_integration.get_tools()
        
        # Get cached repository contexts
        repo_contexts = {}
        if conversation_id:
            repo_contexts = self.conversation_manager.get_all_repo_contexts(conversation_id)
            if repo_contexts:
                logger.info(f"Using cached project structures for {len(repo_contexts)} repositories")
                
                # Add repository contexts to system prompt
                context_text = "\n\n## Repository Context\n\n"
                for repo_key, context in repo_contexts.items():
                    if context:  # Only add non-empty contexts
                        context_text += f"### {repo_key}\n\n{context}\n\n"
                
                if system_prompt:
                    system_prompt = f"{system_prompt}{context_text}"
                else:
                    system_prompt = context_text
        
        try:
            # Send initial message
            response = self.client.create_message(
                messages=messages,
                model=model_id,
                max_tokens=max_tokens,
                system=system_prompt,
                tools=tools
            )
            
            if include_logs:
                emit_log("Prompt verzonden naar Claude")
            
            # Handle tool usage if needed
            if tools and response.stop_reason == "tool_use":
                response = await self.mcp_integration.handle_tool_use(
                    response=response,
                    messages=messages,
                    client=self.client,
                    message_params={
                        "model": model_id,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "system": system_prompt,
                        "tools": tools
                    },
                    log_callback=emit_log if include_logs else None,
                    conversation_id=conversation_id
                )
            
            response_text = response.content[0].text
            if include_logs:
                emit_log("Antwoord van Claude ontvangen")
                
            return response_text
            
        finally:
            # Disconnect from MCP server
            if self.mcp_integration.is_connected:
                await self.mcp_integration.disconnect()
    
    def send_prompt(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        conversation_id: Optional[Union[str, int]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        include_logs: bool = True,
        log_callback: Optional[callable] = None,
        repo_path: Optional[str] = None,  # Kept for backwards compatibility
    ) -> Dict[str, Any]:
        """
        Send a prompt to Claude and return the response.
        
        Args:
            prompt: User prompt to send
            model_id: Optional model identifier
            conversation_id: Conversation ID to continue
            system_prompt: Optional system prompt override
            max_tokens: Maximum output tokens
            include_logs: Whether to capture log messages
            log_callback: Optional callback for log messages
            repo_path: Path to repository (kept for backwards compatibility)
            
        Returns:
            Dictionary with response data and metadata
        """
        # Setup parameters
        model_id = model_id or self.default_model
        system_prompt = system_prompt or self.system_prompt
        
        if max_tokens is None:
            max_tokens = self.get_model_max_tokens(model_id)
            logger.debug(f"Using model-specific max_tokens: {max_tokens} for model: {model_id}")
        
        # Setup logging
        logs: List[str] = []
        
        def emit_log(message: str) -> None:
            if include_logs:
                logs.append(message)
            if log_callback:
                try:
                    log_callback(message)
                except Exception as e:
                    logger.error(f"Log callback failed: {e}")
        
        # Get or create conversation
        if conversation_id is None:
            conversation_id = self.create_conversation()
        
        # Build messages list
        try:
            messages = self.conversation_manager.get_messages_for_api(conversation_id)
        except ValueError:
            # Conversation doesn't exist in memory, try to load from database
            if isinstance(conversation_id, int):
                logger.info(f"Loading conversation {conversation_id} from database")
                # Create conversation in manager
                self.conversation_manager.create_conversation(str(conversation_id))
                # Load messages from database
                try:
                    db_messages = ConversationRepository.get_messages(conversation_id)
                    for msg in db_messages:
                        self.conversation_manager.add_message(
                            conversation_id=str(conversation_id),
                            role=msg.role,
                            content=msg.content
                        )
                    messages = self.conversation_manager.get_messages_for_api(str(conversation_id))
                except Exception as e:
                    logger.error(f"Failed to load conversation from database: {str(e)}")
                    messages = []
            else:
                messages = []
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Combine werkwijze with system prompt if needed
        if self.werkwijze:
            if system_prompt:
                system_prompt = f"{system_prompt}\n\n{self.werkwijze}"
            else:
                system_prompt = self.werkwijze
        
        # Get or create event loop
        loop = ensure_event_loop()
        
        try:
            # Send prompt and get response
            response_text = loop.run_until_complete(
                self._send_prompt_async(
                    messages=messages,
                    model_id=model_id,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                    emit_log=emit_log,
                    include_logs=include_logs,
                    conversation_id=conversation_id
                )
            )
            
            # Add to conversation
            self.add_to_conversation(conversation_id, prompt, response_text)
            
            logger.info(f"Successfully received response from Anthropic API, conversation: {conversation_id}")
            
            return {
                "conversation_id": conversation_id,
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
    
    # Backwards compatibility properties
    @property
    def conversations(self):
        """For backwards compatibility - returns conversation data."""
        return {
            conv_id: [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in conv.messages
            ]
            for conv_id, conv in self.conversation_manager._conversations.items()
        }


def get_anthropic_api():
    """
    Factory function to create an AnthropicAPI instance with the current app's config.
    
    Returns:
        Configured AnthropicAPI instance
    """
    try:
        # Try to get Flask app config
        config_dict = current_app.config.get_anthropic_config_dict()
    except (RuntimeError, AttributeError):
        # Flask app context not available or method doesn't exist
        config_dict = None
    
    return AnthropicAPI(config=config_dict)


# Global instance management
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
    Ensure an asyncio event loop exists.
    
    Returns:
        The current or newly created event loop
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No loop running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # No event loop exists or it's closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    return loop
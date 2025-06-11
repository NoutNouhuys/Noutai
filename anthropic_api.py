import os
import time
import json
import uuid
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union, Any
from flask import current_app
from pathlib import Path

from anthropic_config import AnthropicConfig
from anthropic_client import AnthropicClient
from conversation_manager import ConversationManager
from mcp_integration import MCPIntegration
from repositories.conversation_repository import ConversationRepository
from analytics.token_tracker import TokenTracker
from repository_analyzer import RepositoryAnalyzer, generate_repository_summary

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
        self.mcp_integration = MCPIntegration(self.anthropic_config)
        self.token_tracker = TokenTracker()
        
        # For backwards compatibility
        self.api_key = self.anthropic_config.api_key
        self.default_model = self.anthropic_config.default_model
        self.max_tokens = self.anthropic_config.max_tokens
        self.temperature = self.anthropic_config.temperature
        self.cache_ttl = self.anthropic_config.cache_ttl
        self.system_prompt = self.anthropic_config.system_prompt
        self.werkwijze = self.anthropic_config.werkwijze
        self.project_info = self.anthropic_config.project_info
        
        logger.debug(f"AnthropicAPI initialized with model: {self.default_model}, temperature: {self.temperature}")
    
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
    
    def get_llm_settings(self, model_id: Optional[str] = None, preset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current LLM settings.
        
        Args:
            model_id: Optional model identifier for model-specific settings
            preset_name: Optional preset name to load settings from
            
        Returns:
            Dict with current LLM settings
        """
        return self.client.get_llm_settings(model_id=model_id, preset_name=preset_name)
    
    def get_available_presets(self) -> List[Dict[str, Any]]:
        """
        Get available LLM presets.
        
        Returns:
            List of available presets with their configurations
        """
        return self.client.get_available_presets()
    
    def validate_llm_settings(self, temperature: float, max_tokens: int) -> bool:
        """
        Validate LLM settings.
        
        Args:
            temperature: Temperature value to validate
            max_tokens: Max tokens value to validate
            
        Returns:
            True if settings are valid
            
        Raises:
            ValueError: If settings are invalid
        """
        return self.client.validate_settings(temperature, max_tokens)
    
    def update_runtime_settings(self, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Update runtime LLM settings (doesn't persist).
        
        Args:
            temperature: New temperature value
            max_tokens: New max tokens value
            
        Returns:
            Dict with updated settings
            
        Raises:
            ValueError: If settings are invalid
        """
        current_settings = self.get_llm_settings()
        
        if temperature is not None:
            current_settings['temperature'] = temperature
        if max_tokens is not None:
            current_settings['max_tokens'] = max_tokens
        
        # Validate the updated settings
        self.validate_llm_settings(
            current_settings['temperature'], 
            current_settings['max_tokens']
        )
        
        # Update the config dict for this session
        if temperature is not None:
            self.anthropic_config.config_dict['ANTHROPIC_TEMPERATURE'] = str(temperature)
            self.temperature = temperature
        if max_tokens is not None:
            self.anthropic_config.config_dict['ANTHROPIC_MAX_TOKENS'] = str(max_tokens)
            self.max_tokens = max_tokens
        
        logger.info(f"Runtime LLM settings updated: temperature={current_settings['temperature']}, max_tokens={current_settings['max_tokens']}")
        
        return current_settings
    
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
    
    def get_conversation_analytics(self, conversation_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get analytics data for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            Analytics data for the conversation
        """
        try:
            # Convert to int if needed for database lookup
            conv_id = int(conversation_id) if isinstance(conversation_id, str) and conversation_id.isdigit() else conversation_id
            return self.token_tracker.get_conversation_usage(conv_id)
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {e}")
            return {'error': str(e)}
    
    def generate_repository_summary(self, repo_path: str = ".") -> str:
        """
        Generate a summary of the repository structure and contents.
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            Repository summary as a string
        """
        try:
            logger.info(f"Generating repository summary for: {repo_path}")
            return generate_repository_summary(repo_path)
        except Exception as e:
            logger.error(f"Error generating repository summary: {e}")
            raise
    
    def check_and_generate_repository_summary(self, repo_path: str = ".") -> Optional[str]:
        """
        Check if repository_summary.txt exists and generate it if needed.
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            Path to the summary file if generated, None if already exists
        """
        summary_path = Path(repo_path) / "repository_summary.txt"
        
        if not summary_path.exists():
            logger.info("repository_summary.txt not found, generating...")
            summary_content = self.generate_repository_summary(repo_path)
            
            # Write the summary to file
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            logger.info(f"Generated repository_summary.txt at {summary_path}")
            return str(summary_path)
        else:
            logger.info("repository_summary.txt already exists")
            return None
    
    async def _send_prompt_async(
        self,
        messages: List[Dict[str, Any]],
        model_id: str,
        max_tokens: int,
        temperature: Optional[float],
        system_prompt: Optional[str],
        project_info: Optional[str],
        preset_name: Optional[str],
        emit_log: callable,
        include_logs: bool,
        conversation_id: Union[str, int],
        message_id: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Internal async method to send prompt and handle tool usage.
        
        Args:
            messages: Conversation messages
            model_id: Model to use
            max_tokens: Maximum output tokens
            temperature: Temperature for response generation
            system_prompt: System prompt
            project_info: Project information to include in cache
            preset_name: Optional LLM preset name
            emit_log: Logging callback
            include_logs: Whether to emit logs
            conversation_id: ID of the conversation
            message_id: Optional message ID for tracking
            
        Returns:
            Tuple of (response text, usage data)
        """
        # Connect to MCP server if configured
        tools = []
        if self.anthropic_config.mcp_server_script:
            connected = await self.mcp_integration.connect()
            if connected:
                if include_logs:
                    emit_log("Verbinding met MCP-server opgezet")
                tools = await self.mcp_integration.get_tools()
        
        try:
            # Send initial message
            response = self.client.create_message(
                messages=messages,
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                project_info=project_info,
                preset_name=preset_name,
                tools=tools
            )
            
            if include_logs:
                log_msg = f"Prompt verzonden naar Claude (model: {model_id}"
                if preset_name:
                    log_msg += f", preset: {preset_name}"
                if temperature is not None:
                    log_msg += f", temperature: {temperature}"
                log_msg += ")"
                emit_log(log_msg)
            
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
                        "temperature": temperature,
                        "system": system_prompt,
                        "project_info": project_info,
                        "preset_name": preset_name,
                        "tools": tools
                    },
                    log_callback=emit_log if include_logs else None
                )
            
            response_text = response.content[0].text
            
            # Extract usage data from response
            usage_data = {}
            if hasattr(response, 'usage'):
                usage_data = {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'cache_creation_input_tokens': getattr(response.usage, 'cache_creation_input_tokens', 0),
                    'cache_read_input_tokens': getattr(response.usage, 'cache_read_input_tokens', 0)
                }
                
                # Record token usage
                try:
                    conv_id = int(conversation_id) if isinstance(conversation_id, str) and conversation_id.isdigit() else conversation_id
                    request_metadata = {
                        'model_version': getattr(response, 'model', model_id),
                        'request_type': 'chat',
                        'temperature': temperature,
                        'max_tokens': max_tokens,
                        'preset_used': preset_name
                    }
                    
                    self.token_tracker.record_usage(
                        conversation_id=conv_id,
                        model_name=model_id,
                        usage_data=usage_data,
                        message_id=message_id,
                        request_metadata=request_metadata
                    )
                    
                    if include_logs:
                        total_tokens = usage_data['input_tokens'] + usage_data['output_tokens']
                        emit_log(f"Token gebruik: {total_tokens} tokens (in: {usage_data['input_tokens']}, out: {usage_data['output_tokens']})")
                        
                except Exception as e:
                    logger.error(f"Error recording token usage: {e}")
            
            if include_logs:
                emit_log("Antwoord van Claude ontvangen")
                
            return response_text, usage_data
            
        finally:
            # Disconnect from MCP server
            if self.mcp_integration.is_connected:
                await self.mcp_integration.disconnect()
    
    def _should_include_project_info(self, prompt: str) -> bool:
        """
        Determine if project info should be included based on the prompt.
        
        Args:
            prompt: The user's prompt
            
        Returns:
            True if project info should be included
        """
        # Keywords that suggest development/project-related questions
        dev_keywords = [
            'ga', 'ontwikkel', 'implement', 'module', 'bestand', 'file',
            'code', 'functie', 'function', 'class', 'test', 'bug', 'issue',
            'feature', 'refactor', 'architecture', 'design', 'repository',
            'project', 'status', 'voortgang', 'progress', 'plan'
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in dev_keywords)
    
    def send_prompt(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        conversation_id: Optional[Union[str, int]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        preset_name: Optional[str] = None,
        include_logs: bool = True,
        log_callback: Optional[callable] = None,
        repo_path: Optional[str] = None,
        include_project_info: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Send a prompt to Claude and return the response.
        
        Args:
            prompt: User prompt to send
            model_id: Optional model identifier
            conversation_id: Conversation ID to continue
            system_prompt: Optional system prompt override
            max_tokens: Maximum output tokens
            temperature: Temperature for response generation (0.0-1.0)
            preset_name: Optional LLM preset name to use
            include_logs: Whether to capture log messages
            log_callback: Optional callback for log messages
            repo_path: Path to repository (used for repository summary generation)
            include_project_info: Whether to include project info (auto-detected if None)
            
        Returns:
            Dictionary with response data and metadata
        """
        # Check if this is a development-related prompt and handle repository summary
        if self._should_include_project_info(prompt) and repo_path:
            summary_path = self.check_and_generate_repository_summary(repo_path)
            if summary_path and log_callback:
                log_callback(f"Generated repository_summary.txt at {summary_path}")
        
        # Setup parameters
        model_id = model_id or self.default_model
        system_prompt = system_prompt or self.system_prompt
        
        # If preset is specified, get its settings but allow overrides
        if preset_name:
            preset_settings = self.get_llm_settings(preset_name=preset_name)
            if max_tokens is None:
                max_tokens = preset_settings.get('max_tokens')
            if temperature is None:
                temperature = preset_settings.get('temperature')
        
        # Apply defaults if still None
        if max_tokens is None:
            max_tokens = self.get_model_max_tokens(model_id)
            logger.debug(f"Using model-specific max_tokens: {max_tokens} for model: {model_id}")
        
        if temperature is None:
            temperature = self.temperature
        
        # Validate settings
        self.validate_llm_settings(temperature, max_tokens)
        
        # Determine whether to include project info
        if include_project_info is None:
            include_project_info = self._should_include_project_info(prompt)
        
        project_info = self.project_info if include_project_info else None
        
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
            # Send prompt and get response with usage data
            response_text, usage_data = loop.run_until_complete(
                self._send_prompt_async(
                    messages=messages,
                    model_id=model_id,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                    project_info=project_info,
                    preset_name=preset_name,
                    emit_log=emit_log,
                    include_logs=include_logs,
                    conversation_id=conversation_id
                )
            )
            
            # Add to conversation
            self.add_to_conversation(conversation_id, prompt, response_text)
            
            logger.info(f"Successfully received response from Anthropic API, conversation: {conversation_id}")
            if project_info:
                logger.debug("Included project_info in the request")
            if preset_name:
                logger.debug(f"Used LLM preset: {preset_name}")
            
            return {
                "conversation_id": conversation_id,
                "message": response_text,
                "model": model_id,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "preset_name": preset_name,
                "usage": usage_data,
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
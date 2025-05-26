"""
Anthropic API client module.
Handles pure API communication with Claude models.
"""
import logging
from typing import Dict, List, Optional, Any, Protocol
import anthropic
from anthropic_config import AnthropicConfig

logger = logging.getLogger(__name__)


class IAnthropicClient(Protocol):
    """Interface for Anthropic client implementations."""
    
    async def send_message(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Send messages to the Anthropic API."""
        ...


class AnthropicClient:
    """Client for communicating with the Anthropic API."""
    
    def __init__(self, config: AnthropicConfig):
        """
        Initialize the Anthropic client.
        
        Args:
            config: AnthropicConfig instance
        """
        self.config = config
        self._client = None
        
    @property
    def client(self) -> anthropic.Anthropic:
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.config.api_key)
        return self._client
    
    def create_message(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None,
        project_info: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> anthropic.types.Message:
        """
        Create a message using the Anthropic API.
        
        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to config default)
            max_tokens: Maximum tokens for response
            system: System prompt
            project_info: Project information to include in cache
            tools: Available tools for the model
            **kwargs: Additional parameters for the API
            
        Returns:
            Message response from the API
        """
        model = model or self.config.default_model
        
        if max_tokens is None:
            max_tokens = self.config.get_model_max_tokens(model)
            
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        # Build system prompts array with caching
        system_parts = []
        
        if system:
            system_parts.append({
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            })
            
        if project_info:
            # Add project info to the cached system context
            system_parts.append({
                "type": "text",
                "text": f"\n\n# Project Information\n{project_info}",
                "cache_control": {"type": "ephemeral"},
            })
            
        if system_parts:
            params["system"] = system_parts
            
        if tools:
            params["tools"] = tools
            
        logger.debug(f"Sending message to Anthropic API with model: {model}, max_tokens: {max_tokens}")
        if project_info:
            logger.debug("Including project_info in ephemeral cache")
        
        try:
            response = self.client.messages.create(**params)
            logger.info(f"Successfully received response from Anthropic API")
            return response
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            raise
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models.
        
        Returns:
            List of model configurations
        """
        return self.config.available_models
    
    def get_model_max_tokens(self, model_id: str) -> int:
        """
        Get maximum tokens for a specific model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Maximum tokens for the model
        """
        return self.config.get_model_max_tokens(model_id)
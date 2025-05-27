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
        temperature: Optional[float] = None,
        system: Optional[str] = None,
        project_info: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        preset_name: Optional[str] = None,
        **kwargs
    ) -> anthropic.types.Message:
        """
        Create a message using the Anthropic API.
        
        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to config default)
            max_tokens: Maximum tokens for response (overrides config/preset)
            temperature: Temperature for response (overrides config/preset)
            system: System prompt
            project_info: Project information to include in cache
            tools: Available tools for the model
            preset_name: Optional LLM preset to load settings from
            **kwargs: Additional parameters for the API
            
        Returns:
            Message response from the API
        """
        model = model or self.config.default_model
        
        # Get LLM settings from preset or config, then apply overrides
        if preset_name:
            llm_settings = self.config.get_llm_settings(preset_name=preset_name)
        else:
            llm_settings = self.config.get_model_specific_settings(model)
        
        # Apply parameter overrides
        final_temperature = temperature if temperature is not None else llm_settings.get('temperature')
        final_max_tokens = max_tokens if max_tokens is not None else llm_settings.get('max_tokens')
        
        # Validate settings before API call
        if final_temperature is not None:
            self.config.validate_llm_settings(final_temperature, final_max_tokens)
        
        # Ensure max_tokens doesn't exceed model limits
        model_max_tokens = self.config.get_model_max_tokens(model)
        final_max_tokens = min(final_max_tokens, model_max_tokens)
            
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": final_max_tokens,
            **kwargs
        }
        
        # Add temperature if provided
        if final_temperature is not None:
            params["temperature"] = final_temperature
        
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
            
        logger.debug(
            f"Sending message to Anthropic API with model: {model}, "
            f"max_tokens: {final_max_tokens}, temperature: {final_temperature}"
        )
        if project_info:
            logger.debug("Including project_info in ephemeral cache")
        if preset_name:
            logger.debug(f"Using LLM preset: {preset_name}")
        
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
    
    def get_llm_settings(self, model_id: Optional[str] = None, preset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current LLM settings for a model or preset.
        
        Args:
            model_id: Optional model identifier for model-specific settings
            preset_name: Optional preset name to load settings from
            
        Returns:
            Dict with current LLM settings
        """
        if preset_name:
            return self.config.get_llm_settings(preset_name=preset_name)
        elif model_id:
            return self.config.get_model_specific_settings(model_id)
        else:
            return self.config.get_llm_settings()
    
    def get_available_presets(self) -> List[Dict[str, Any]]:
        """
        Get available LLM presets.
        
        Returns:
            List of available presets with their configurations
        """
        return self.config.get_available_presets()
    
    def validate_settings(self, temperature: float, max_tokens: int) -> bool:
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
        return self.config.validate_llm_settings(temperature, max_tokens)
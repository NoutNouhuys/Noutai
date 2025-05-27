"""
Anthropic-specific configuration module.
Centralizes all Anthropic API related configuration.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from functools import cached_property

logger = logging.getLogger(__name__)


class AnthropicConfig:
    """Configuration class specifically for Anthropic API settings."""
    
    # LLM Settings presets
    LLM_PRESETS = {
        "developer_agent": {
            "name": "Python Developer Agent",
            "temperature": 0.2,
            "max_tokens": 4000,
            "description": "Optimized for code generation and development tasks"
        },
        "creative_writing": {
            "name": "Creative Writing",
            "temperature": 0.8,
            "max_tokens": 8000,
            "description": "Higher creativity for writing and storytelling"
        },
        "analysis": {
            "name": "Data Analysis",
            "temperature": 0.1,
            "max_tokens": 6000,
            "description": "Low temperature for analytical and factual tasks"
        },
        "balanced": {
            "name": "Balanced",
            "temperature": 0.5,
            "max_tokens": 4000,
            "description": "Balanced settings for general purpose use"
        }
    }
    
    def __init__(self, api_key: Optional[str] = None, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize Anthropic configuration.
        
        Args:
            api_key: Optional API key override
            config_dict: Optional configuration dictionary
        """
        self.config_dict = config_dict or {}
        self._api_key = api_key
        self._base_path = os.path.dirname(__file__)
        
    @property
    def api_key(self) -> str:
        """Get the Anthropic API key with validation."""
        key = self._api_key or self.config_dict.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
        if not key:
            raise ValueError("Anthropic API key is required but not provided")
        return key
    
    @property
    def default_model(self) -> str:
        """Get the default model."""
        return self.config_dict.get('ANTHROPIC_DEFAULT_MODEL') or os.environ.get('ANTHROPIC_DEFAULT_MODEL') or 'claude-3-haiku-20240307'
    
    @property
    def temperature(self) -> float:
        """Get the LLM temperature setting with validation."""
        temp = self.config_dict.get('ANTHROPIC_TEMPERATURE') or os.environ.get('ANTHROPIC_TEMPERATURE')
        if temp is not None:
            temp = float(temp)
        else:
            # Default to developer agent preset (0.2) for Python development
            temp = 0.2
        
        # Validate temperature range
        if not 0.0 <= temp <= 1.0:
            raise ValueError(f"Temperature must be between 0.0 and 1.0, got {temp}")
        
        return temp
    
    @property
    def max_tokens(self) -> int:
        """Get the default maximum tokens."""
        tokens = self.config_dict.get('ANTHROPIC_MAX_TOKENS') or os.environ.get('ANTHROPIC_MAX_TOKENS')
        if tokens is not None:
            tokens = int(tokens)
        else:
            tokens = 4000
        
        # Validate max tokens
        if tokens <= 0:
            raise ValueError(f"Max tokens must be greater than 0, got {tokens}")
        
        return tokens
    
    @property
    def cache_ttl(self) -> str:
        """Get the cache TTL setting."""
        return self.config_dict.get('ANTHROPIC_CACHE_TTL') or os.environ.get('ANTHROPIC_CACHE_TTL', '5m')
    
    def get_llm_settings(self, preset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get LLM settings, optionally from a preset.
        
        Args:
            preset_name: Optional preset name to load settings from
            
        Returns:
            Dict with LLM settings (temperature, max_tokens, etc.)
        """
        if preset_name and preset_name in self.LLM_PRESETS:
            preset = self.LLM_PRESETS[preset_name].copy()
            # Remove metadata fields
            settings = {k: v for k, v in preset.items() if k not in ['name', 'description']}
        else:
            settings = {
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            }
        
        return settings
    
    def get_available_presets(self) -> List[Dict[str, Any]]:
        """Get all available LLM presets."""
        return [
            {
                "id": preset_id,
                **preset_config
            }
            for preset_id, preset_config in self.LLM_PRESETS.items()
        ]
    
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
        if not 0.0 <= temperature <= 1.0:
            raise ValueError(f"Temperature must be between 0.0 and 1.0, got {temperature}")
        
        if max_tokens <= 0:
            raise ValueError(f"Max tokens must be greater than 0, got {max_tokens}")
        
        return True
    
    def get_model_specific_settings(self, model_id: str) -> Dict[str, Any]:
        """
        Get model-specific LLM settings.
        
        Args:
            model_id: The model identifier
            
        Returns:
            Dict with model-specific settings
        """
        model_config = self.get_model_config(model_id)
        if not model_config:
            return self.get_llm_settings()
        
        # Start with general settings
        settings = self.get_llm_settings()
        
        # Apply model-specific max_tokens limit
        model_max_tokens = model_config.get('max_tokens', settings['max_tokens'])
        settings['max_tokens'] = min(settings['max_tokens'], model_max_tokens)
        
        return settings
    
    @cached_property
    def system_prompt(self) -> Optional[str]:
        """Lazy load system prompt from file."""
        # Check if already in config dict
        if 'ANTHROPIC_SYSTEM_PROMPT' in self.config_dict:
            return self.config_dict['ANTHROPIC_SYSTEM_PROMPT']
            
        # Try to load from file
        system_prompt_path = os.path.join(self._base_path, 'system_prompt.txt')
        try:
            with open(system_prompt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.warning(f"system_prompt.txt not found at {system_prompt_path}")
            return None
    
    @cached_property
    def werkwijze(self) -> Optional[str]:
        """Lazy load werkwijze from file."""
        # Check if already in config dict
        if 'ANTHROPIC_WERKWIJZE' in self.config_dict:
            return self.config_dict['ANTHROPIC_WERKWIJZE']
            
        # Try to load from file
        werkwijze_path = os.path.join(self._base_path, 'werkwijze', 'werkwijze.txt')
        try:
            with open(werkwijze_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.warning(f"werkwijze.txt not found at {werkwijze_path}")
            return None
    
    @cached_property
    def project_info(self) -> Optional[str]:
        """Lazy load project info from file."""
        # Check if already in config dict
        if 'ANTHROPIC_PROJECT_INFO' in self.config_dict:
            return self.config_dict['ANTHROPIC_PROJECT_INFO']
            
        # Try to load from file
        project_info_path = os.path.join(self._base_path, 'project_info.txt')
        try:
            with open(project_info_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.warning(f"project_info.txt not found at {project_info_path}")
            return None
    
    @property
    def available_models(self) -> List[Dict[str, Any]]:
        """Get available models configuration."""
        # This could be loaded from a config file in the future
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
                "name": "Claude 3.7 Sonnet",
                "description": "Current most intelligent model",
                "context_length": 200000,
                "max_tokens": 20480,
            },
            {
                "id": "claude-sonnet-4-20250514",
                "name": "Claude 4 Sonnet",
                "description": "Improved reasoning and intelligence capabilities compared to Claude Sonnet 3.7",
                "context_length": 200000,
                "max_tokens": 20480,
            },
            {
                "id": "claude-opus-4-20250514",
                "name": "Claude 4 Opus",
                "description": "Most capable model with superior reasoning and intelligence, Slower than Sonnet models,Best for complex tasks requiring deep analysis",
                "context_length": 200000,
                "max_tokens": 20480,
            }
        ]
    
    def get_model_config(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific model."""
        for model in self.available_models:
            if model["id"] == model_id:
                return model
        return None
    
    def get_model_max_tokens(self, model_id: str) -> int:
        """Get max tokens for a specific model."""
        model_config = self.get_model_config(model_id)
        if model_config:
            return model_config.get("max_tokens", self.max_tokens)
        logger.warning(f"Model {model_id} not found, using default max_tokens: {self.max_tokens}")
        return self.max_tokens
    
    def validate(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        try:
            # This will raise if API key is missing
            _ = self.api_key
            
            # Validate LLM settings
            self.validate_llm_settings(self.temperature, self.max_tokens)
            
            return True
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    @property 
    def mcp_servers(self) -> List[str]:
        """Get MCP server configuration."""
        servers = self.config_dict.get('MCP_SERVERS') or os.getenv("MCP_SERVERS", "")
        if isinstance(servers, str):
            return [s.strip() for s in servers.split(",") if s.strip()]
        return servers or []
    
    @property
    def mcp_server_script(self) -> Optional[str]:
        """Get MCP server script path."""
        return os.environ.get("MCP_SERVER_SCRIPT")
    
    @property
    def mcp_server_venv_path(self) -> Optional[str]:
        """Get MCP server virtual environment path."""
        return os.environ.get("MCP_SERVER_VENV_PATH")
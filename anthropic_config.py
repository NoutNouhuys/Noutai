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
            "max_tokens": 20000,
            "description": "Optimized for code generation and development tasks"
        },
        "creative_writing": {
            "name": "Creative Writing",
            "temperature": 0.8,
            "max_tokens": 10000,
            "description": "Higher creativity for writing and storytelling"
        },
        "analysis": {
            "name": "Data Analysis",
            "temperature": 0.1,
            "max_tokens": 10000,
            "description": "Low temperature for analytical and factual tasks"
        },
        "balanced": {
            "name": "Balanced",
            "temperature": 0.5,
            "max_tokens": 10000,
            "description": "Balanced settings for general purpose use"
        }
    }
    
    # Platform types
    PLATFORM_GITHUB = "github"
    PLATFORM_BITBUCKET = "bitbucket"
    
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
                 "id": "claude-opus-4-20250514",
                "name": "Claude Opus 4",
                "description": "Most powerful model for complex tasks, best coding model in the world",
                "context_length": 200000,
                "max_tokens": 20000,
            },
            {
                "id": "claude-sonnet-4-20250514",
                "name": "Claude Sonnet 4",
                "description": "Excellent balance of intelligence and speed for production workloads",
                "context_length": 200000,
                "max_tokens": 20000,
            },
            {
                "id": "claude-3-5-haiku-20241022",
                "name": "Claude 3.5 Haiku",
                "description": "Fastest model for simpler tasks",
                "context_length": 200000,
                "max_tokens": 8192,
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
    
    # Platform Configuration Properties
    
    @property
    def default_platform(self) -> str:
        """Get the default platform (github or bitbucket)."""
        return self.config_dict.get('DEFAULT_PLATFORM') or os.environ.get('DEFAULT_PLATFORM', self.PLATFORM_GITHUB)
    
    @property
    def supported_platforms(self) -> List[str]:
        """Get list of supported platforms."""
        return [self.PLATFORM_GITHUB, self.PLATFORM_BITBUCKET]
    
    def is_platform_supported(self, platform: str) -> bool:
        """Check if a platform is supported."""
        return platform.lower() in self.supported_platforms
    
    # GitHub Configuration Properties
    
    @property 
    def mcp_servers(self) -> List[str]:
        """Get MCP server configuration."""
        servers = self.config_dict.get('MCP_SERVERS') or os.getenv("MCP_SERVERS", "")
        if isinstance(servers, str):
            return [s.strip() for s in servers.split(",") if s.strip()]
        return servers or []
    
    @property
    def mcp_server_script(self) -> Optional[str]:
        """Get GitHub MCP server script path."""
        return os.environ.get("MCP_SERVER_SCRIPT")
    
    @property
    def mcp_server_venv_path(self) -> Optional[str]:
        """Get GitHub MCP server virtual environment path."""
        return os.environ.get("MCP_SERVER_VENV_PATH")
    
    # Bitbucket Configuration Properties
    
    @property
    def bitbucket_workspace(self) -> Optional[str]:
        """Get Bitbucket workspace."""
        return self.config_dict.get('BITBUCKET_WORKSPACE') or os.environ.get('BITBUCKET_WORKSPACE')
    
    @property
    def bitbucket_username(self) -> Optional[str]:
        """Get Bitbucket username."""
        return self.config_dict.get('BITBUCKET_USERNAME') or os.environ.get('BITBUCKET_USERNAME')
    
    @property
    def bitbucket_app_password(self) -> Optional[str]:
        """Get Bitbucket app password."""
        return self.config_dict.get('BITBUCKET_APP_PASSWORD') or os.environ.get('BITBUCKET_APP_PASSWORD')
    
    def is_bitbucket_configured(self) -> bool:
        """Check if Bitbucket is properly configured."""
        return all([
            self.bitbucket_workspace,
            self.bitbucket_username,
            self.bitbucket_app_password
        ])
    
    def is_github_configured(self) -> bool:
        """Check if GitHub is properly configured."""
        return bool(self.mcp_server_script)
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """
        Get configuration for a specific platform.
        
        Args:
            platform: Platform name (github or bitbucket)
            
        Returns:
            Dict with platform-specific configuration
        """
        if platform.lower() == self.PLATFORM_GITHUB:
            return {
                'platform': self.PLATFORM_GITHUB,
                'configured': self.is_github_configured(),
                'mcp_server_script': self.mcp_server_script,
                'mcp_server_venv_path': self.mcp_server_venv_path
            }
        elif platform.lower() == self.PLATFORM_BITBUCKET:
            return {
                'platform': self.PLATFORM_BITBUCKET,
                'configured': self.is_bitbucket_configured(),
                'workspace': self.bitbucket_workspace,
                'username': self.bitbucket_username,
                'has_app_password': bool(self.bitbucket_app_password)
            }
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    def get_available_platforms(self) -> List[Dict[str, Any]]:
        """Get list of available platforms with their configuration status."""
        platforms = []
        
        for platform in self.supported_platforms:
            config = self.get_platform_config(platform)
            platforms.append({
                'id': platform,
                'name': platform.title(),
                'configured': config['configured'],
                'default': platform == self.default_platform
            })
        
        return platforms
    
    def detect_platform_from_repo(self, repo_identifier: str) -> Optional[str]:
        """
        Detect platform from repository identifier.
        
        Args:
            repo_identifier: Repository identifier (e.g., "owner/repo" or "workspace/repo_slug")
            
        Returns:
            Platform name or None if cannot be detected
        """
        # This is a simple heuristic - in practice you might want more sophisticated detection
        # For now, we'll use the default platform unless explicitly specified
        return self.default_platform
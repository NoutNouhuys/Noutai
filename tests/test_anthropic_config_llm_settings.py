"""
Unit tests for AnthropicConfig LLM settings functionality.
"""
import os
import pytest
from unittest.mock import patch, mock_open
from anthropic_config import AnthropicConfig


class TestAnthropicConfigLLMSettings:
    """Test LLM settings functionality in AnthropicConfig."""
    
    def test_default_temperature(self):
        """Test default temperature setting (0.2 for developer agent)."""
        config = AnthropicConfig()
        assert config.temperature == 0.2
    
    def test_temperature_from_env(self):
        """Test temperature loading from environment variable."""
        with patch.dict(os.environ, {'ANTHROPIC_TEMPERATURE': '0.8'}):
            config = AnthropicConfig()
            assert config.temperature == 0.8
    
    def test_temperature_from_config_dict(self):
        """Test temperature loading from config dictionary."""
        config_dict = {'ANTHROPIC_TEMPERATURE': '0.1'}
        config = AnthropicConfig(config_dict=config_dict)
        assert config.temperature == 0.1
    
    def test_temperature_validation_valid_range(self):
        """Test temperature validation with valid values."""
        config = AnthropicConfig()
        
        # Test boundaries and mid-range values
        with patch.dict(os.environ, {'ANTHROPIC_TEMPERATURE': '0.0'}):
            config = AnthropicConfig()
            assert config.temperature == 0.0
            
        with patch.dict(os.environ, {'ANTHROPIC_TEMPERATURE': '1.0'}):
            config = AnthropicConfig()
            assert config.temperature == 1.0
            
        with patch.dict(os.environ, {'ANTHROPIC_TEMPERATURE': '0.5'}):
            config = AnthropicConfig()
            assert config.temperature == 0.5
    
    def test_temperature_validation_invalid_range(self):
        """Test temperature validation with invalid values."""
        with patch.dict(os.environ, {'ANTHROPIC_TEMPERATURE': '-0.1'}):
            config = AnthropicConfig()
            with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
                _ = config.temperature
                
        with patch.dict(os.environ, {'ANTHROPIC_TEMPERATURE': '1.1'}):
            config = AnthropicConfig()
            with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
                _ = config.temperature
    
    def test_max_tokens_from_env(self):
        """Test max_tokens loading from environment variable."""
        with patch.dict(os.environ, {'ANTHROPIC_MAX_TOKENS': '8000'}):
            config = AnthropicConfig()
            assert config.max_tokens == 8000
    
    def test_max_tokens_validation_valid(self):
        """Test max_tokens validation with valid values."""
        with patch.dict(os.environ, {'ANTHROPIC_MAX_TOKENS': '1000'}):
            config = AnthropicConfig()
            assert config.max_tokens == 1000
    
    def test_max_tokens_validation_invalid(self):
        """Test max_tokens validation with invalid values."""
        with patch.dict(os.environ, {'ANTHROPIC_MAX_TOKENS': '0'}):
            config = AnthropicConfig()
            with pytest.raises(ValueError, match="Max tokens must be greater than 0"):
                _ = config.max_tokens
                
        with patch.dict(os.environ, {'ANTHROPIC_MAX_TOKENS': '-100'}):
            config = AnthropicConfig()
            with pytest.raises(ValueError, match="Max tokens must be greater than 0"):
                _ = config.max_tokens
    
    def test_get_llm_settings_default(self):
        """Test getting default LLM settings."""
        config = AnthropicConfig()
        settings = config.get_llm_settings()
        
        assert 'temperature' in settings
        assert 'max_tokens' in settings
        assert settings['temperature'] == 0.2
        assert settings['max_tokens'] == 4000
    
    def test_get_llm_settings_with_preset(self):
        """Test getting LLM settings from preset."""
        config = AnthropicConfig()
        
        # Test developer agent preset
        settings = config.get_llm_settings(preset_name='developer_agent')
        assert settings['temperature'] == 0.2
        assert settings['max_tokens'] == 4000
        
        # Test creative writing preset
        settings = config.get_llm_settings(preset_name='creative_writing')
        assert settings['temperature'] == 0.8
        assert settings['max_tokens'] == 8000
        
        # Test analysis preset
        settings = config.get_llm_settings(preset_name='analysis')
        assert settings['temperature'] == 0.1
        assert settings['max_tokens'] == 6000
    
    def test_get_llm_settings_invalid_preset(self):
        """Test getting LLM settings with invalid preset name."""
        config = AnthropicConfig()
        settings = config.get_llm_settings(preset_name='invalid_preset')
        
        # Should fall back to default settings
        assert settings['temperature'] == 0.2
        assert settings['max_tokens'] == 4000
    
    def test_get_available_presets(self):
        """Test getting available LLM presets."""
        config = AnthropicConfig()
        presets = config.get_available_presets()
        
        assert len(presets) >= 4  # We have at least 4 presets
        
        # Check that each preset has required fields
        for preset in presets:
            assert 'id' in preset
            assert 'name' in preset
            assert 'temperature' in preset
            assert 'max_tokens' in preset
            assert 'description' in preset
        
        # Check specific presets exist
        preset_ids = [p['id'] for p in presets]
        assert 'developer_agent' in preset_ids
        assert 'creative_writing' in preset_ids
        assert 'analysis' in preset_ids
        assert 'balanced' in preset_ids
    
    def test_validate_llm_settings_valid(self):
        """Test LLM settings validation with valid values."""
        config = AnthropicConfig()
        
        # Valid combinations
        assert config.validate_llm_settings(0.2, 4000) is True
        assert config.validate_llm_settings(0.0, 1) is True
        assert config.validate_llm_settings(1.0, 8192) is True
    
    def test_validate_llm_settings_invalid_temperature(self):
        """Test LLM settings validation with invalid temperature."""
        config = AnthropicConfig()
        
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
            config.validate_llm_settings(-0.1, 4000)
            
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
            config.validate_llm_settings(1.1, 4000)
    
    def test_validate_llm_settings_invalid_max_tokens(self):
        """Test LLM settings validation with invalid max_tokens."""
        config = AnthropicConfig()
        
        with pytest.raises(ValueError, match="Max tokens must be greater than 0"):
            config.validate_llm_settings(0.5, 0)
            
        with pytest.raises(ValueError, match="Max tokens must be greater than 0"):
            config.validate_llm_settings(0.5, -100)
    
    def test_get_model_specific_settings(self):
        """Test getting model-specific LLM settings."""
        config = AnthropicConfig()
        
        # Test with known model
        settings = config.get_model_specific_settings('claude-3-opus-20240229')
        assert 'temperature' in settings
        assert 'max_tokens' in settings
        
        # Max tokens should be limited by model max
        assert settings['max_tokens'] <= 4096  # Opus max tokens
        
        # Test with unknown model
        settings = config.get_model_specific_settings('unknown-model')
        assert settings['temperature'] == 0.2  # Default
        assert settings['max_tokens'] == 4000  # Default
    
    def test_get_model_specific_settings_with_override(self):
        """Test model-specific settings with higher default max_tokens."""
        with patch.dict(os.environ, {'ANTHROPIC_MAX_TOKENS': '10000'}):
            config = AnthropicConfig()
            
            # Should be limited by model max (4096 for Opus)
            settings = config.get_model_specific_settings('claude-3-opus-20240229')
            assert settings['max_tokens'] == 4096
            
            # Should use full amount for models with higher limits
            settings = config.get_model_specific_settings('claude-3-sonnet-20240229')
            assert settings['max_tokens'] == 8192  # Sonnet max tokens
    
    def test_config_validation_includes_llm_settings(self):
        """Test that config validation includes LLM settings validation."""
        # Valid config
        config = AnthropicConfig(api_key='test-key')
        assert config.validate() is True
        
        # Invalid temperature
        with patch.dict(os.environ, {'ANTHROPIC_TEMPERATURE': '2.0'}):
            config = AnthropicConfig(api_key='test-key')
            with pytest.raises(ValueError):
                config.validate()
        
        # Invalid max_tokens
        with patch.dict(os.environ, {'ANTHROPIC_MAX_TOKENS': '-1'}):
            config = AnthropicConfig(api_key='test-key')
            with pytest.raises(ValueError):
                config.validate()
    
    def test_preset_structure(self):
        """Test that preset structure contains all required fields."""
        config = AnthropicConfig()
        
        for preset_id, preset_config in config.LLM_PRESETS.items():
            # Check required fields
            assert 'name' in preset_config
            assert 'temperature' in preset_config
            assert 'max_tokens' in preset_config
            assert 'description' in preset_config
            
            # Validate temperature range
            temp = preset_config['temperature']
            assert isinstance(temp, (int, float))
            assert 0.0 <= temp <= 1.0
            
            # Validate max_tokens
            max_tokens = preset_config['max_tokens']
            assert isinstance(max_tokens, int)
            assert max_tokens > 0
    
    def test_llm_settings_without_metadata(self):
        """Test that get_llm_settings excludes metadata fields."""
        config = AnthropicConfig()
        settings = config.get_llm_settings(preset_name='developer_agent')
        
        # Should not include metadata fields
        assert 'name' not in settings
        assert 'description' not in settings
        
        # Should only include actual settings
        assert 'temperature' in settings
        assert 'max_tokens' in settings
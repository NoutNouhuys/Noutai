"""Tests for AnthropicConfig module."""
import os
import unittest
from unittest.mock import patch, mock_open
from anthropic_config import AnthropicConfig


class TestAnthropicConfig(unittest.TestCase):
    """Test cases for AnthropicConfig class."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear any existing environment variables
        self.env_vars = {
            'ANTHROPIC_API_KEY': None,
            'ANTHROPIC_DEFAULT_MODEL': None,
            'ANTHROPIC_MAX_TOKENS': None,
            'ANTHROPIC_CACHE_TTL': None,
            'MCP_SERVERS': None,
        }
        for var in self.env_vars:
            if var in os.environ:
                self.env_vars[var] = os.environ[var]
                del os.environ[var]
    
    def tearDown(self):
        """Restore environment."""
        for var, value in self.env_vars.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
    
    def test_api_key_from_parameter(self):
        """Test API key from parameter takes precedence."""
        config = AnthropicConfig(api_key="test-key-param")
        self.assertEqual(config.api_key, "test-key-param")
    
    def test_api_key_from_config_dict(self):
        """Test API key from config dictionary."""
        config = AnthropicConfig(config_dict={'ANTHROPIC_API_KEY': 'test-key-dict'})
        self.assertEqual(config.api_key, "test-key-dict")
    
    def test_api_key_from_environment(self):
        """Test API key from environment variable."""
        os.environ['ANTHROPIC_API_KEY'] = 'test-key-env'
        config = AnthropicConfig()
        self.assertEqual(config.api_key, "test-key-env")
    
    def test_api_key_missing_raises_error(self):
        """Test missing API key raises ValueError."""
        config = AnthropicConfig()
        with self.assertRaises(ValueError) as context:
            _ = config.api_key
        self.assertIn("API key is required", str(context.exception))
    
    def test_default_model(self):
        """Test default model configuration."""
        config = AnthropicConfig()
        self.assertEqual(config.default_model, 'claude-3-haiku-20240307')
        
        # Test from environment
        os.environ['ANTHROPIC_DEFAULT_MODEL'] = 'claude-3-opus-20240229'
        config = AnthropicConfig()
        self.assertEqual(config.default_model, 'claude-3-opus-20240229')
    
    def test_max_tokens(self):
        """Test max tokens configuration."""
        config = AnthropicConfig()
        self.assertEqual(config.max_tokens, 4000)
        
        # Test from config dict
        config = AnthropicConfig(config_dict={'ANTHROPIC_MAX_TOKENS': 8000})
        self.assertEqual(config.max_tokens, 8000)
    
    def test_cache_ttl(self):
        """Test cache TTL configuration."""
        config = AnthropicConfig()
        self.assertEqual(config.cache_ttl, '5m')
        
        # Test from environment
        os.environ['ANTHROPIC_CACHE_TTL'] = '10m'
        config = AnthropicConfig()
        self.assertEqual(config.cache_ttl, '10m')
    
    @patch('builtins.open', new_callable=mock_open, read_data='Test system prompt')
    def test_system_prompt_lazy_loading(self, mock_file):
        """Test lazy loading of system prompt."""
        config = AnthropicConfig()
        
        # Should not load until accessed
        mock_file.assert_not_called()
        
        # Access the property
        prompt = config.system_prompt
        self.assertEqual(prompt, 'Test system prompt')
        mock_file.assert_called_once()
        
        # Second access should use cached value
        prompt2 = config.system_prompt
        self.assertEqual(prompt2, 'Test system prompt')
        mock_file.assert_called_once()  # Still only called once
    
    def test_system_prompt_from_config_dict(self):
        """Test system prompt from config dictionary."""
        config = AnthropicConfig(config_dict={'ANTHROPIC_SYSTEM_PROMPT': 'Config prompt'})
        self.assertEqual(config.system_prompt, 'Config prompt')
    
    def test_available_models(self):
        """Test available models configuration."""
        config = AnthropicConfig()
        models = config.available_models
        
        self.assertIsInstance(models, list)
        self.assertTrue(len(models) > 0)
        
        # Check model structure
        for model in models:
            self.assertIn('id', model)
            self.assertIn('name', model)
            self.assertIn('description', model)
            self.assertIn('context_length', model)
            self.assertIn('max_tokens', model)
    
    def test_get_model_config(self):
        """Test getting configuration for specific model."""
        config = AnthropicConfig()
        
        # Test existing model
        model_config = config.get_model_config('claude-3-haiku-20240307')
        self.assertIsNotNone(model_config)
        self.assertEqual(model_config['id'], 'claude-3-haiku-20240307')
        
        # Test non-existing model
        model_config = config.get_model_config('non-existent-model')
        self.assertIsNone(model_config)
    
    def test_get_model_max_tokens(self):
        """Test getting max tokens for specific model."""
        config = AnthropicConfig()
        
        # Test existing model
        max_tokens = config.get_model_max_tokens('claude-3-opus-20240229')
        self.assertEqual(max_tokens, 20480)
        
        # Test non-existing model returns default
        max_tokens = config.get_model_max_tokens('non-existent-model')
        self.assertEqual(max_tokens, config.max_tokens)
    
    def test_validate_success(self):
        """Test successful validation."""
        config = AnthropicConfig(api_key='test-key')
        self.assertTrue(config.validate())
    
    def test_validate_failure(self):
        """Test validation failure."""
        config = AnthropicConfig()
        with self.assertRaises(ValueError):
            config.validate()
    
    def test_mcp_servers(self):
        """Test MCP servers configuration."""
        config = AnthropicConfig()
        self.assertEqual(config.mcp_servers, [])
        
        # Test from environment
        os.environ['MCP_SERVERS'] = 'server1,server2,server3'
        config = AnthropicConfig()
        self.assertEqual(config.mcp_servers, ['server1', 'server2', 'server3'])
        
        # Test with spaces
        os.environ['MCP_SERVERS'] = ' server1 , server2 , server3 '
        config = AnthropicConfig()
        self.assertEqual(config.mcp_servers, ['server1', 'server2', 'server3'])
    
    def test_mcp_server_paths(self):
        """Test MCP server path configuration."""
        config = AnthropicConfig()
        self.assertIsNone(config.mcp_server_script)
        self.assertIsNone(config.mcp_server_venv_path)
        
        # Test from environment
        os.environ['MCP_SERVER_SCRIPT'] = '/path/to/script.py'
        os.environ['MCP_SERVER_VENV_PATH'] = '/path/to/venv'
        config = AnthropicConfig()
        self.assertEqual(config.mcp_server_script, '/path/to/script.py')
        self.assertEqual(config.mcp_server_venv_path, '/path/to/venv')


if __name__ == '__main__':
    unittest.main()
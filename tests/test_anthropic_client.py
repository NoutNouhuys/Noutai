"""Tests for AnthropicClient module."""
import unittest
from unittest.mock import Mock, patch, MagicMock
from anthropic_client import AnthropicClient
from anthropic_config import AnthropicConfig


class TestAnthropicClient(unittest.TestCase):
    """Test cases for AnthropicClient class."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_config = Mock(spec=AnthropicConfig)
        self.mock_config.api_key = "test-api-key"
        self.mock_config.default_model = "claude-3-haiku-20240307"
        self.mock_config.get_model_max_tokens.return_value = 4096
        self.mock_config.available_models = []
        self.mock_config.validate_llm_settings.return_value = True
        self.mock_config.get_llm_settings.return_value = {
            'temperature': 0.2,
            'max_tokens': 4000
        }
        self.mock_config.get_model_specific_settings.return_value = {
            'temperature': 0.2,
            'max_tokens': 4000
        }
        
        self.client = AnthropicClient(self.mock_config)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_lazy_client_initialization(self, mock_anthropic):
        """Test that Anthropic client is lazily initialized."""
        # Client should not be created yet
        mock_anthropic.assert_not_called()
        
        # Access the client property
        _ = self.client.client
        
        # Now it should be created
        mock_anthropic.assert_called_once_with(api_key="test-api-key")
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_with_system_prompt(self, mock_anthropic):
        """Test create_message with system prompt."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        messages = [{"role": "user", "content": "Hello"}]
        system_prompt = "You are a helpful assistant"
        
        self.client.create_message(
            messages=messages,
            system=system_prompt
        )
        
        # Verify the system prompt is added with cache control
        expected_params = {
            "model": "claude-3-haiku-20240307",
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        }
        
        mock_client.messages.create.assert_called_once_with(**expected_params)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_with_temperature(self, mock_anthropic):
        """Test create_message with custom temperature."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        messages = [{"role": "user", "content": "Hello"}]
        temperature = 0.8
        
        self.client.create_message(
            messages=messages,
            temperature=temperature
        )
        
        # Verify temperature is used and validation is called
        self.mock_config.validate_llm_settings.assert_called_once_with(0.8, 4000)
        
        expected_params = {
            "model": "claude-3-haiku-20240307",
            "messages": messages,
            "max_tokens": 4000,
            "temperature": temperature
        }
        
        mock_client.messages.create.assert_called_once_with(**expected_params)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_with_preset(self, mock_anthropic):
        """Test create_message with LLM preset."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Configure mock to return preset settings
        preset_settings = {'temperature': 0.8, 'max_tokens': 8000}
        self.mock_config.get_llm_settings.return_value = preset_settings
        
        messages = [{"role": "user", "content": "Hello"}]
        preset_name = "creative_writing"
        
        self.client.create_message(
            messages=messages,
            preset_name=preset_name
        )
        
        # Verify preset settings are loaded and used
        self.mock_config.get_llm_settings.assert_called_once_with(preset_name=preset_name)
        self.mock_config.validate_llm_settings.assert_called_once_with(0.8, 8000)
        
        expected_params = {
            "model": "claude-3-haiku-20240307",
            "messages": messages,
            "max_tokens": 8000,
            "temperature": 0.8
        }
        
        mock_client.messages.create.assert_called_once_with(**expected_params)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_parameter_override(self, mock_anthropic):
        """Test that direct parameters override preset settings."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Configure mock to return preset settings
        preset_settings = {'temperature': 0.8, 'max_tokens': 8000}
        self.mock_config.get_llm_settings.return_value = preset_settings
        
        messages = [{"role": "user", "content": "Hello"}]
        preset_name = "creative_writing"
        override_temperature = 0.1
        override_max_tokens = 2000
        
        self.client.create_message(
            messages=messages,
            preset_name=preset_name,
            temperature=override_temperature,
            max_tokens=override_max_tokens
        )
        
        # Verify overrides are used instead of preset values
        self.mock_config.validate_llm_settings.assert_called_once_with(0.1, 2000)
        
        expected_params = {
            "model": "claude-3-haiku-20240307",
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        mock_client.messages.create.assert_called_once_with(**expected_params)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_model_max_tokens_limit(self, mock_anthropic):
        """Test that max_tokens is limited by model capabilities."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Configure model to have lower max tokens than requested
        self.mock_config.get_model_max_tokens.return_value = 2000
        
        messages = [{"role": "user", "content": "Hello"}]
        requested_max_tokens = 8000
        
        self.client.create_message(
            messages=messages,
            max_tokens=requested_max_tokens
        )
        
        # Verify max_tokens is limited to model capacity
        expected_params = {
            "model": "claude-3-haiku-20240307",
            "messages": messages,
            "max_tokens": 2000,  # Limited by model
            "temperature": 0.2
        }
        
        mock_client.messages.create.assert_called_once_with(**expected_params)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_validation_error(self, mock_anthropic):
        """Test that validation errors are raised properly."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Configure validation to raise error
        self.mock_config.validate_llm_settings.side_effect = ValueError("Invalid temperature")
        
        messages = [{"role": "user", "content": "Hello"}]
        
        with self.assertRaises(ValueError) as context:
            self.client.create_message(
                messages=messages,
                temperature=1.5  # Invalid temperature
            )
        
        self.assertEqual(str(context.exception), "Invalid temperature")
        mock_client.messages.create.assert_not_called()
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_with_project_info(self, mock_anthropic):
        """Test create_message with project info."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        messages = [{"role": "user", "content": "Hello"}]
        system_prompt = "You are a helpful assistant"
        project_info = "This is project information"
        
        self.client.create_message(
            messages=messages,
            system=system_prompt,
            project_info=project_info
        )
        
        # Verify both system prompt and project info are added with cache control
        expected_params = {
            "model": "claude-3-haiku-20240307",
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": "\n\n# Project Information\nThis is project information",
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        }
        
        mock_client.messages.create.assert_called_once_with(**expected_params)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_with_only_project_info(self, mock_anthropic):
        """Test create_message with only project info (no system prompt)."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        messages = [{"role": "user", "content": "Hello"}]
        project_info = "This is project information"
        
        self.client.create_message(
            messages=messages,
            project_info=project_info
        )
        
        # Verify project info is added with cache control
        expected_params = {
            "model": "claude-3-haiku-20240307",
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": [
                {
                    "type": "text",
                    "text": "\n\n# Project Information\nThis is project information",
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        }
        
        mock_client.messages.create.assert_called_once_with(**expected_params)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_with_tools(self, mock_anthropic):
        """Test create_message with tools."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"name": "test_tool", "description": "A test tool"}]
        
        self.client.create_message(
            messages=messages,
            tools=tools
        )
        
        # Verify tools are passed correctly
        expected_params = {
            "model": "claude-3-haiku-20240307",
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.2,
            "tools": tools
        }
        
        mock_client.messages.create.assert_called_once_with(**expected_params)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_with_custom_model(self, mock_anthropic):
        """Test create_message with custom model."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        messages = [{"role": "user", "content": "Hello"}]
        custom_model = "claude-3-opus-20240229"
        
        self.client.create_message(
            messages=messages,
            model=custom_model
        )
        
        # Verify custom model is used
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        self.assertEqual(call_args["model"], custom_model)
    
    @patch('anthropic_client.anthropic.Anthropic')
    def test_create_message_error_handling(self, mock_anthropic):
        """Test error handling in create_message."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")
        
        messages = [{"role": "user", "content": "Hello"}]
        
        with self.assertRaises(Exception) as context:
            self.client.create_message(messages=messages)
        
        self.assertEqual(str(context.exception), "API Error")
    
    def test_get_available_models(self):
        """Test get_available_models."""
        expected_models = [
            {"id": "model1", "name": "Model 1"},
            {"id": "model2", "name": "Model 2"}
        ]
        self.mock_config.available_models = expected_models
        
        models = self.client.get_available_models()
        self.assertEqual(models, expected_models)
    
    def test_get_model_max_tokens(self):
        """Test get_model_max_tokens."""
        model_id = "claude-3-opus-20240229"
        expected_tokens = 20480
        self.mock_config.get_model_max_tokens.return_value = expected_tokens
        
        tokens = self.client.get_model_max_tokens(model_id)
        
        self.assertEqual(tokens, expected_tokens)
        self.mock_config.get_model_max_tokens.assert_called_once_with(model_id)
    
    def test_get_llm_settings_default(self):
        """Test get_llm_settings with default parameters."""
        expected_settings = {'temperature': 0.2, 'max_tokens': 4000}
        self.mock_config.get_llm_settings.return_value = expected_settings
        
        settings = self.client.get_llm_settings()
        
        self.assertEqual(settings, expected_settings)
        self.mock_config.get_llm_settings.assert_called_once_with()
    
    def test_get_llm_settings_with_model(self):
        """Test get_llm_settings with model_id."""
        model_id = "claude-3-opus-20240229"
        expected_settings = {'temperature': 0.1, 'max_tokens': 4096}
        self.mock_config.get_model_specific_settings.return_value = expected_settings
        
        settings = self.client.get_llm_settings(model_id=model_id)
        
        self.assertEqual(settings, expected_settings)
        self.mock_config.get_model_specific_settings.assert_called_once_with(model_id)
    
    def test_get_llm_settings_with_preset(self):
        """Test get_llm_settings with preset_name."""
        preset_name = "creative_writing"
        expected_settings = {'temperature': 0.8, 'max_tokens': 8000}
        self.mock_config.get_llm_settings.return_value = expected_settings
        
        settings = self.client.get_llm_settings(preset_name=preset_name)
        
        self.assertEqual(settings, expected_settings)
        self.mock_config.get_llm_settings.assert_called_once_with(preset_name=preset_name)
    
    def test_get_available_presets(self):
        """Test get_available_presets."""
        expected_presets = [
            {"id": "developer_agent", "name": "Python Developer Agent"},
            {"id": "creative_writing", "name": "Creative Writing"}
        ]
        self.mock_config.get_available_presets.return_value = expected_presets
        
        presets = self.client.get_available_presets()
        
        self.assertEqual(presets, expected_presets)
        self.mock_config.get_available_presets.assert_called_once()
    
    def test_validate_settings(self):
        """Test validate_settings."""
        temperature = 0.5
        max_tokens = 4000
        
        result = self.client.validate_settings(temperature, max_tokens)
        
        self.assertTrue(result)
        self.mock_config.validate_llm_settings.assert_called_once_with(temperature, max_tokens)
    
    def test_validate_settings_error(self):
        """Test validate_settings with invalid values."""
        self.mock_config.validate_llm_settings.side_effect = ValueError("Invalid settings")
        
        with self.assertRaises(ValueError) as context:
            self.client.validate_settings(1.5, -100)
        
        self.assertEqual(str(context.exception), "Invalid settings")


if __name__ == '__main__':
    unittest.main()
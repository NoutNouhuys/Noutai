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
            "max_tokens": 4096,
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
            "max_tokens": 4096,
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
            "max_tokens": 4096,
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
            "max_tokens": 4096,
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


if __name__ == '__main__':
    unittest.main()
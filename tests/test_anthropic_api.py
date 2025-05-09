import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic_api import AnthropicAPI


class TestAnthropicAPI(unittest.TestCase):
    """Test cases for the Anthropic API module"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test API key for use in tests
        os.environ['ANTHROPIC_API_KEY'] = 'test-api-key'
        
        # Create the API instance with the test key
        self.api = AnthropicAPI(api_key='test-api-key')
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove the test API key
        if 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']
    
    def test_get_available_models(self):
        """Test getting available models"""
        models = self.api.get_available_models()
        
        # Check that models is a list
        self.assertIsInstance(models, list)
        
        # Check that each model has the required fields
        for model in models:
            self.assertIn('id', model)
            self.assertIn('name', model)
            self.assertIn('description', model)
            self.assertIn('context_length', model)
    
    def test_create_conversation(self):
        """Test creating a new conversation"""
        conversation_id = self.api.create_conversation()
        
        # Check that a conversation ID is returned and is a string
        self.assertIsInstance(conversation_id, str)
        
        # Check that the conversation exists in the internal store
        self.assertIn(conversation_id, self.api.conversations)
        
        # Check that the conversation is initialized as an empty list
        self.assertEqual(self.api.conversations[conversation_id], [])
    
    def test_get_conversation(self):
        """Test retrieving a conversation"""
        # Create a conversation
        conversation_id = self.api.create_conversation()
        
        # Get the conversation
        conversation = self.api.get_conversation(conversation_id)
        
        # Check that the conversation is a list
        self.assertIsInstance(conversation, list)
        
        # Check that the conversation is empty
        self.assertEqual(len(conversation), 0)
        
        # Test getting a non-existent conversation
        with self.assertRaises(ValueError):
            self.api.get_conversation('non-existent-id')
    
    def test_add_to_conversation(self):
        """Test adding messages to a conversation"""
        # Create a conversation
        conversation_id = self.api.create_conversation()
        
        # Add messages to the conversation
        self.api.add_to_conversation(conversation_id, 'Hello, Claude', 'Hello, how can I help you?')
        
        # Get the conversation
        conversation = self.api.get_conversation(conversation_id)
        
        # Check that there are now two messages in the conversation
        self.assertEqual(len(conversation), 2)
        
        # Check the message properties
        self.assertEqual(conversation[0]['role'], 'user')
        self.assertEqual(conversation[0]['content'], 'Hello, Claude')
        self.assertEqual(conversation[1]['role'], 'assistant')
        self.assertEqual(conversation[1]['content'], 'Hello, how can I help you?')
        
        # Test adding to a non-existent conversation
        with self.assertRaises(ValueError):
            self.api.add_to_conversation('non-existent-id', 'Hello', 'Hi')
    
    @patch('anthropic.Anthropic')
    def test_send_prompt(self, mock_anthropic):
        """Test sending a prompt to Claude"""
        # Mock the Anthropic client and its methods
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Set up the mock response
        mock_content = MagicMock()
        mock_content.text = "This is a test response from Claude."
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        
        # Send a test prompt
        response = self.api.send_prompt("Test prompt", "claude-3-haiku-20240307")
        
        # Check that the mock was called with the right parameters
        mock_client.messages.create.assert_called_once()
        
        # Check the response structure
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], "This is a test response from Claude.")
        self.assertEqual(response['model'], "claude-3-haiku-20240307")
        self.assertIn('conversation_id', response)
        
        # Test error handling
        mock_client.messages.create.side_effect = Exception("Test error")
        
        # Send another prompt that will raise an error
        response = self.api.send_prompt("Error prompt", "claude-3-haiku-20240307")
        
        # Check that the response indicates failure
        self.assertFalse(response['success'])
        self.assertEqual(response['error'], "Test error")


if __name__ == '__main__':
    unittest.main()

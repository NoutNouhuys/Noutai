"""Tests for ConversationManager module."""
import unittest
from unittest.mock import Mock, patch
import time
from conversation_manager import ConversationManager, Conversation, Message


class TestConversationManager(unittest.TestCase):
    """Test cases for ConversationManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.manager = ConversationManager()
    
    def test_create_conversation_with_auto_id(self):
        """Test creating conversation with auto-generated ID."""
        conv_id = self.manager.create_conversation()
        self.assertIsNotNone(conv_id)
        self.assertTrue(self.manager.exists(conv_id))
    
    def test_create_conversation_with_specific_id(self):
        """Test creating conversation with specific ID."""
        conv_id = "test-conv-123"
        result_id = self.manager.create_conversation(conv_id)
        self.assertEqual(result_id, conv_id)
        self.assertTrue(self.manager.exists(conv_id))
    
    def test_add_message(self):
        """Test adding a message to conversation."""
        conv_id = self.manager.create_conversation()
        
        self.manager.add_message(conv_id, "user", "Hello, Claude!")
        
        messages = self.manager.get_messages(conv_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Hello, Claude!")
    
    def test_add_message_to_nonexistent_conversation(self):
        """Test adding message to non-existent conversation raises error."""
        with self.assertRaises(ValueError) as context:
            self.manager.add_message("non-existent", "user", "Hello")
        self.assertIn("not found", str(context.exception))
    
    def test_add_exchange(self):
        """Test adding a user-assistant exchange."""
        conv_id = self.manager.create_conversation()
        
        self.manager.add_exchange(
            conv_id,
            "What is 2+2?",
            "2+2 equals 4."
        )
        
        messages = self.manager.get_messages(conv_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "What is 2+2?")
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[1].content, "2+2 equals 4.")
    
    def test_get_conversation(self):
        """Test getting a conversation."""
        conv_id = self.manager.create_conversation()
        self.manager.add_message(conv_id, "user", "Test message")
        
        conversation = self.manager.get_conversation(conv_id)
        self.assertIsInstance(conversation, Conversation)
        self.assertEqual(conversation.id, conv_id)
        self.assertEqual(len(conversation.messages), 1)
    
    def test_get_nonexistent_conversation(self):
        """Test getting non-existent conversation raises error."""
        with self.assertRaises(ValueError) as context:
            self.manager.get_conversation("non-existent")
        self.assertIn("not found", str(context.exception))
    
    def test_get_messages_for_api(self):
        """Test getting messages formatted for API."""
        conv_id = self.manager.create_conversation()
        self.manager.add_exchange(
            conv_id,
            "Hello",
            "Hi there!"
        )
        
        api_messages = self.manager.get_messages_for_api(conv_id)
        self.assertEqual(len(api_messages), 2)
        self.assertEqual(api_messages[0], {"role": "user", "content": "Hello"})
        self.assertEqual(api_messages[1], {"role": "assistant", "content": "Hi there!"})
    
    def test_exists(self):
        """Test checking if conversation exists."""
        conv_id = self.manager.create_conversation()
        
        self.assertTrue(self.manager.exists(conv_id))
        self.assertFalse(self.manager.exists("non-existent"))
    
    def test_clear(self):
        """Test clearing all conversations."""
        # Create multiple conversations
        conv_id1 = self.manager.create_conversation()
        conv_id2 = self.manager.create_conversation()
        
        self.assertTrue(self.manager.exists(conv_id1))
        self.assertTrue(self.manager.exists(conv_id2))
        
        # Clear all
        self.manager.clear()
        
        self.assertFalse(self.manager.exists(conv_id1))
        self.assertFalse(self.manager.exists(conv_id2))
    
    def test_conversation_with_int_id(self):
        """Test handling conversation with integer ID."""
        int_id = 123
        str_id = str(int_id)
        
        # Create with string version
        self.manager.create_conversation(str_id)
        
        # Should be able to access with int or string
        self.assertTrue(self.manager.exists(int_id))
        self.assertTrue(self.manager.exists(str_id))
        
        # Add message with int ID
        self.manager.add_message(int_id, "user", "Test")
        
        # Get messages with string ID
        messages = self.manager.get_messages(str_id)
        self.assertEqual(len(messages), 1)
    
    @patch('conversation_manager.ConversationRepository')
    def test_load_from_storage(self, mock_repo):
        """Test loading conversation from storage backend."""
        # Setup mock
        mock_message = Mock()
        mock_message.role = "user"
        mock_message.content = "Stored message"
        mock_message.created_at.timestamp.return_value = time.time()
        
        mock_repo.get_messages.return_value = [mock_message]
        
        # Create manager with storage backend
        manager = ConversationManager(storage_backend=True)
        
        # Try to get conversation with integer ID
        conversation = manager.get_conversation(123)
        
        self.assertEqual(conversation.id, "123")
        self.assertEqual(len(conversation.messages), 1)
        self.assertEqual(conversation.messages[0].content, "Stored message")
    
    def test_message_metadata(self):
        """Test message metadata handling."""
        conv_id = self.manager.create_conversation()
        
        metadata = {"model": "claude-3-opus", "temperature": 0.7}
        self.manager.add_message(conv_id, "user", "Test", metadata=metadata)
        
        messages = self.manager.get_messages(conv_id)
        self.assertEqual(messages[0].metadata, metadata)
    
    def test_conversation_metadata(self):
        """Test conversation metadata."""
        conv_id = self.manager.create_conversation()
        conversation = self.manager.get_conversation(conv_id)
        
        # Check default metadata
        self.assertIsInstance(conversation.metadata, dict)
        self.assertIsInstance(conversation.created_at, float)


if __name__ == '__main__':
    unittest.main()
"""
Unit tests for the enhanced ConversationManager module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from conversation_manager import ConversationManager, Conversation, Message


class TestConversationManager(unittest.TestCase):
    """Test cases for ConversationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user_id = "test_user_123"
        
        # Create manager without storage backend for basic tests
        self.manager = ConversationManager()
        
        # Create manager with mocked storage backend for persistence tests
        self.storage_manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        
    def test_initialization_without_storage(self):
        """Test initialization without storage backend."""
        manager = ConversationManager()
        
        self.assertIsNone(manager.storage_backend)
        self.assertIsNone(manager.user_id)
        self.assertEqual(len(manager._conversations), 0)
        self.assertIsNone(manager.repository)
        
    def test_initialization_with_storage(self):
        """Test initialization with storage backend."""
        with patch('conversation_manager.ConversationRepository') as mock_repo:
            manager = ConversationManager(storage_backend=True, user_id=self.user_id)
            
            self.assertTrue(manager.storage_backend)
            self.assertEqual(manager.user_id, self.user_id)
            self.assertEqual(len(manager._conversations), 0)
            self.assertEqual(manager.repository, mock_repo)
    
    def test_create_conversation_in_memory(self):
        """Test creating a conversation without database."""
        conv_id = self.manager.create_conversation(title="Test Conversation")
        
        self.assertIsNotNone(conv_id)
        self.assertIn(conv_id, self.manager._conversations)
        
        conversation = self.manager._conversations[conv_id]
        self.assertEqual(conversation.title, "Test Conversation")
        self.assertEqual(conversation.id, conv_id)
        
    def test_create_conversation_with_custom_id(self):
        """Test creating a conversation with custom ID."""
        custom_id = "custom_123"
        conv_id = self.manager.create_conversation(conversation_id=custom_id)
        
        self.assertEqual(conv_id, custom_id)
        self.assertIn(custom_id, self.manager._conversations)
        
    @patch('conversation_manager.ConversationRepository')
    def test_create_conversation_with_database(self, mock_repo_class):
        """Test creating a conversation with database storage."""
        # Setup mocks
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        mock_db_conversation = Mock()
        mock_db_conversation.id = 42
        mock_repo.save_conversation.return_value = mock_db_conversation
        
        manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        manager.repository = mock_repo
        
        # Create conversation
        conv_id = manager.create_conversation(title="Test", model="claude-3-haiku")
        
        # Verify database call
        mock_repo.save_conversation.assert_called_once_with(
            self.user_id, 
            {'title': 'Test', 'model': 'claude-3-haiku'}
        )
        
        # Verify in-memory storage
        self.assertEqual(conv_id, "42")
        self.assertIn("42", manager._conversations)
        
    def test_add_message(self):
        """Test adding a message to a conversation."""
        conv_id = self.manager.create_conversation()
        
        self.manager.add_message(conv_id, "user", "Hello!")
        
        messages = self.manager.get_messages(conv_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Hello!")
        
    def test_add_message_with_metadata(self):
        """Test adding a message with metadata."""
        conv_id = self.manager.create_conversation()
        metadata = {"timestamp": time.time(), "model": "claude-3"}
        
        self.manager.add_message(conv_id, "assistant", "Hi there!", metadata)
        
        messages = self.manager.get_messages(conv_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].metadata, metadata)
        
    def test_add_message_nonexistent_conversation(self):
        """Test adding a message to a non-existent conversation."""
        with self.assertRaises(ValueError):
            self.manager.add_message("nonexistent", "user", "Hello!")
            
    @patch('conversation_manager.ConversationRepository')
    def test_add_message_with_database(self, mock_repo_class):
        """Test adding a message with database persistence."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        mock_db_message = Mock()
        mock_repo.save_message.return_value = mock_db_message
        
        manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        manager.repository = mock_repo
        
        # Create conversation and add message
        conv_id = manager.create_conversation()
        manager.add_message(conv_id, "user", "Test message")
        
        # Verify database call
        mock_repo.save_message.assert_called_once_with(
            int(conv_id),
            {
                'role': 'user',
                'content': 'Test message',
                'metadata': None
            }
        )
        
    def test_add_exchange(self):
        """Test adding a user-assistant exchange."""
        conv_id = self.manager.create_conversation()
        
        self.manager.add_exchange(conv_id, "Hello!", "Hi there!")
        
        messages = self.manager.get_messages(conv_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Hello!")
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[1].content, "Hi there!")
        
    def test_get_messages_for_api(self):
        """Test getting messages formatted for API."""
        conv_id = self.manager.create_conversation()
        self.manager.add_exchange(conv_id, "Hello!", "Hi there!")
        
        api_messages = self.manager.get_messages_for_api(conv_id)
        
        self.assertEqual(len(api_messages), 2)
        self.assertEqual(api_messages[0], {"role": "user", "content": "Hello!"})
        self.assertEqual(api_messages[1], {"role": "assistant", "content": "Hi there!"})
        
    def test_exists_conversation(self):
        """Test checking if a conversation exists."""
        conv_id = self.manager.create_conversation()
        
        self.assertTrue(self.manager.exists(conv_id))
        self.assertFalse(self.manager.exists("nonexistent"))
        
    @patch('conversation_manager.ConversationRepository')
    def test_exists_conversation_database(self, mock_repo_class):
        """Test checking conversation existence with database."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        mock_db_conversation = Mock()
        mock_db_conversation.is_active = True
        mock_repo.get_conversation.return_value = mock_db_conversation
        
        manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        manager.repository = mock_repo
        
        # Test existing conversation
        self.assertTrue(manager.exists(123))
        mock_repo.get_conversation.assert_called_with(123)
        
        # Test non-existing conversation
        mock_repo.get_conversation.return_value = None
        self.assertFalse(manager.exists(456))
        
    @patch('conversation_manager.ConversationRepository')
    def test_list_conversations_database(self, mock_repo_class):
        """Test listing conversations from database."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock database conversations
        mock_conv1 = Mock()
        mock_conv1.to_dict.return_value = {"id": 1, "title": "Conv 1"}
        mock_conv2 = Mock()
        mock_conv2.to_dict.return_value = {"id": 2, "title": "Conv 2"}
        
        mock_repo.get_conversations.return_value = [mock_conv1, mock_conv2]
        
        manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        manager.repository = mock_repo
        
        # Test listing with pagination
        conversations = manager.list_conversations(active_only=True, limit=10, offset=0)
        
        mock_repo.get_conversations.assert_called_once_with(self.user_id, True)
        self.assertEqual(len(conversations), 2)
        self.assertEqual(conversations[0]["id"], 1)
        self.assertEqual(conversations[1]["id"], 2)
        
    def test_list_conversations_in_memory(self):
        """Test listing conversations from in-memory storage."""
        # Create test conversations
        conv_id1 = self.manager.create_conversation(title="Conv 1")
        conv_id2 = self.manager.create_conversation(title="Conv 2")
        
        conversations = self.manager.list_conversations()
        
        self.assertEqual(len(conversations), 2)
        titles = [conv["title"] for conv in conversations]
        self.assertIn("Conv 1", titles)
        self.assertIn("Conv 2", titles)
        
    @patch('conversation_manager.ConversationRepository')
    def test_search_conversations_database(self, mock_repo_class):
        """Test searching conversations in database."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock search results
        mock_conv = Mock()
        mock_conv.title = "Test conversation"
        mock_conv.to_dict.return_value = {"id": 1, "title": "Test conversation"}
        
        mock_repo.get_conversations.return_value = [mock_conv]
        
        manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        manager.repository = mock_repo
        
        results = manager.search_conversations("test", limit=10)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test conversation")
        
    def test_search_conversations_in_memory(self):
        """Test searching conversations in memory."""
        # Create test conversations
        conv_id1 = self.manager.create_conversation(title="Python development")
        conv_id2 = self.manager.create_conversation(title="JavaScript project")
        conv_id3 = self.manager.create_conversation(title="Data analysis")
        
        # Add some messages
        self.manager.add_message(conv_id1, "user", "Python code help")
        self.manager.add_message(conv_id2, "user", "React components")
        
        # Search by title
        results = self.manager.search_conversations("python")
        self.assertEqual(len(results), 1)
        self.assertIn("Python development", results[0]["title"])
        
        # Search by message content
        results = self.manager.search_conversations("code")
        self.assertEqual(len(results), 1)
        
    @patch('conversation_manager.ConversationRepository')
    def test_update_conversation(self, mock_repo_class):
        """Test updating conversation metadata."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        mock_updated_conv = Mock()
        mock_repo.update_conversation.return_value = mock_updated_conv
        
        manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        manager.repository = mock_repo
        
        # Create and update conversation
        conv_id = manager.create_conversation()
        success = manager.update_conversation(conv_id, title="New Title", is_active=False)
        
        self.assertTrue(success)
        mock_repo.update_conversation.assert_called_once_with(
            int(conv_id),
            {"title": "New Title", "is_active": False}
        )
        
    @patch('conversation_manager.ConversationRepository')
    def test_delete_conversation_soft(self, mock_repo_class):
        """Test soft deleting a conversation."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.delete_conversation.return_value = True
        
        manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        manager.repository = mock_repo
        
        conv_id = manager.create_conversation()
        success = manager.delete_conversation(conv_id, soft_delete=True)
        
        self.assertTrue(success)
        mock_repo.delete_conversation.assert_called_once_with(int(conv_id))
        
    @patch('conversation_manager.ConversationRepository')
    def test_delete_conversation_hard(self, mock_repo_class):
        """Test hard deleting a conversation."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.hard_delete_conversation.return_value = True
        
        manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        manager.repository = mock_repo
        
        conv_id = manager.create_conversation()
        success = manager.delete_conversation(conv_id, soft_delete=False)
        
        self.assertTrue(success)
        mock_repo.hard_delete_conversation.assert_called_once_with(int(conv_id))
        
    @patch('conversation_manager.ConversationRepository')
    def test_load_conversation_from_database(self, mock_repo_class):
        """Test loading a conversation from database."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock database response
        mock_result = {
            'conversation': {
                'id': 123,
                'title': 'Test Conversation',
                'model': 'claude-3-haiku',
                'is_active': True
            },
            'messages': [
                {
                    'role': 'user',
                    'content': 'Hello',
                    'created_at': '2023-01-01T10:00:00',
                    'metadata': {}
                },
                {
                    'role': 'assistant',
                    'content': 'Hi there!',
                    'created_at': '2023-01-01T10:01:00',
                    'metadata': {}
                }
            ]
        }
        
        mock_repo.get_conversation_with_messages.return_value = mock_result
        
        manager = ConversationManager(storage_backend=True, user_id=self.user_id)
        manager.repository = mock_repo
        
        # Test loading
        success = manager._load_conversation_if_needed(123)
        
        self.assertTrue(success)
        self.assertIn("123", manager._conversations)
        
        conversation = manager._conversations["123"]
        self.assertEqual(conversation.title, "Test Conversation")
        self.assertEqual(len(conversation.messages), 2)
        
    def test_clear_conversations(self):
        """Test clearing all conversations."""
        # Create some conversations
        self.manager.create_conversation()
        self.manager.create_conversation()
        
        self.assertEqual(len(self.manager._conversations), 2)
        
        self.manager.clear()
        
        self.assertEqual(len(self.manager._conversations), 0)
        
    def test_conversation_dataclass(self):
        """Test Conversation dataclass functionality."""
        conversation = Conversation(
            id="test_123",
            title="Test Conversation",
            model="claude-3-haiku"
        )
        
        self.assertEqual(conversation.id, "test_123")
        self.assertEqual(conversation.title, "Test Conversation")
        self.assertEqual(conversation.model, "claude-3-haiku")
        self.assertTrue(conversation.is_active)
        self.assertEqual(len(conversation.messages), 0)
        
    def test_message_dataclass(self):
        """Test Message dataclass functionality."""
        metadata = {"model": "claude-3", "tokens": 100}
        message = Message(
            role="user",
            content="Hello!",
            metadata=metadata
        )
        
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello!")
        self.assertEqual(message.metadata, metadata)
        self.assertIsInstance(message.timestamp, float)
        
    def test_error_handling_database_failure(self):
        """Test error handling when database operations fail."""
        with patch('conversation_manager.ConversationRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            
            # Simulate database failure
            mock_repo.save_conversation.return_value = None
            
            manager = ConversationManager(storage_backend=True, user_id=self.user_id)
            manager.repository = mock_repo
            
            # Should raise exception when database creation fails
            with self.assertRaises(RuntimeError):
                manager.create_conversation()
                
    def test_backwards_compatibility_string_conversation_id(self):
        """Test backwards compatibility with string conversation IDs."""
        conv_id = self.manager.create_conversation("string_id")
        
        self.assertEqual(conv_id, "string_id")
        self.assertTrue(self.manager.exists("string_id"))
        
        self.manager.add_message("string_id", "user", "Test")
        messages = self.manager.get_messages("string_id")
        self.assertEqual(len(messages), 1)


if __name__ == '__main__':
    unittest.main()
"""
Unit tests for the database module.
"""

import unittest
import os
import tempfile
from flask import Flask
from database import init_db, db
from models.conversation import Conversation, Message
from repositories.conversation_repository import ConversationRepository


class TestDatabase(unittest.TestCase):
    """
    Test cases for the database module.
    """
    
    def setUp(self):
        """Set up a test environment with a temporary database."""
        # Create a test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
        # Create a temporary file for the test database
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize the database with the test app
        with self.app.app_context():
            init_db(self.app)
            
        # Create an application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_create_conversation(self):
        """Test creating a new conversation."""
        # Arrange
        user_id = 'test_user'
        conversation_data = {
            'title': 'Test Conversation',
            'model': 'claude-3-opus-20240229'
        }
        
        # Act
        conversation = ConversationRepository.save_conversation(
            user_id=user_id,
            conversation_data=conversation_data
        )
        
        # Assert
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.user_id, user_id)
        self.assertEqual(conversation.title, conversation_data['title'])
        self.assertEqual(conversation.model, conversation_data['model'])
        self.assertTrue(conversation.is_active)
    
    def test_get_conversations(self):
        """Test retrieving conversations for a user."""
        # Arrange
        user_id = 'test_user'
        
        # Create multiple conversations
        for i in range(3):
            conversation = Conversation(
                user_id=user_id,
                title=f'Test Conversation {i+1}',
                model='claude-3-opus-20240229'
            )
            db.session.add(conversation)
        
        # Create inactive conversation
        inactive_conversation = Conversation(
            user_id=user_id,
            title='Inactive Conversation',
            model='claude-3-opus-20240229'
        )
        inactive_conversation.is_active = False
        db.session.add(inactive_conversation)
        
        # Create conversation for different user
        other_conversation = Conversation(
            user_id='other_user',
            title='Other User Conversation',
            model='claude-3-opus-20240229'
        )
        db.session.add(other_conversation)
        
        db.session.commit()
        
        # Act
        active_conversations = ConversationRepository.get_conversations(user_id, active_only=True)
        all_conversations = ConversationRepository.get_conversations(user_id, active_only=False)
        
        # Assert
        self.assertEqual(len(active_conversations), 3)
        self.assertEqual(len(all_conversations), 4)
        
        # Verify all returned conversations belong to the user
        for conversation in all_conversations:
            self.assertEqual(conversation.user_id, user_id)
    
    def test_get_conversation(self):
        """Test retrieving a specific conversation."""
        # Arrange
        user_id = 'test_user'
        conversation = Conversation(
            user_id=user_id,
            title='Test Conversation',
            model='claude-3-opus-20240229'
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Act
        retrieved_conversation = ConversationRepository.get_conversation(conversation.id)
        
        # Assert
        self.assertIsNotNone(retrieved_conversation)
        self.assertEqual(retrieved_conversation.id, conversation.id)
        self.assertEqual(retrieved_conversation.user_id, user_id)
        self.assertEqual(retrieved_conversation.title, 'Test Conversation')
    
    def test_update_conversation(self):
        """Test updating a conversation."""
        # Arrange
        user_id = 'test_user'
        conversation = Conversation(
            user_id=user_id,
            title='Original Title',
            model='claude-3-opus-20240229'
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Act
        updated = ConversationRepository.update_conversation(
            conversation_id=conversation.id,
            conversation_data={
                'title': 'Updated Title',
                'model': 'claude-3-sonnet-20240229'
            }
        )
        
        # Assert
        self.assertIsNotNone(updated)
        self.assertEqual(updated.title, 'Updated Title')
        self.assertEqual(updated.model, 'claude-3-sonnet-20240229')
        
        # Verify changes persisted to database
        fresh_conversation = Conversation.query.get(conversation.id)
        self.assertEqual(fresh_conversation.title, 'Updated Title')
        self.assertEqual(fresh_conversation.model, 'claude-3-sonnet-20240229')
    
    def test_delete_conversation(self):
        """Test soft-deleting a conversation."""
        # Arrange
        user_id = 'test_user'
        conversation = Conversation(
            user_id=user_id,
            title='To Be Deleted',
            model='claude-3-opus-20240229'
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Act
        success = ConversationRepository.delete_conversation(conversation.id)
        
        # Assert
        self.assertTrue(success)
        
        # Verify conversation was soft-deleted
        deleted_conversation = Conversation.query.get(conversation.id)
        self.assertIsNotNone(deleted_conversation)  # Still exists
        self.assertFalse(deleted_conversation.is_active)  # But marked inactive
    
    def test_hard_delete_conversation(self):
        """Test permanently deleting a conversation."""
        # Arrange
        user_id = 'test_user'
        conversation = Conversation(
            user_id=user_id,
            title='To Be Permanently Deleted',
            model='claude-3-opus-20240229'
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Act
        success = ConversationRepository.hard_delete_conversation(conversation.id)
        
        # Assert
        self.assertTrue(success)
        
        # Verify conversation was permanently deleted
        deleted_conversation = Conversation.query.get(conversation.id)
        self.assertIsNone(deleted_conversation)
    
    def test_save_message(self):
        """Test saving a message to a conversation."""
        # Arrange
        user_id = 'test_user'
        conversation = Conversation(
            user_id=user_id,
            title='Conversation with Messages',
            model='claude-3-opus-20240229'
        )
        db.session.add(conversation)
        db.session.commit()
        
        message_data = {
            'role': 'user',
            'content': 'Hello, Claude!',
            'metadata': {'timestamp': '2025-03-02T12:00:00Z'}
        }
        
        # Act
        message = ConversationRepository.save_message(
            conversation_id=conversation.id,
            message_data=message_data
        )
        
        # Assert
        self.assertIsNotNone(message)
        self.assertEqual(message.conversation_id, conversation.id)
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.content, 'Hello, Claude!')
        self.assertIn('timestamp', message.metadata)
    
    def test_get_messages(self):
        """Test retrieving messages for a conversation."""
        # Arrange
        user_id = 'test_user'
        conversation = Conversation(
            user_id=user_id,
            title='Conversation with Messages',
            model='claude-3-opus-20240229'
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Add messages
        messages = [
            Message(
                conversation_id=conversation.id,
                role='user',
                content='Hello, Claude!'
            ),
            Message(
                conversation_id=conversation.id,
                role='assistant',
                content='Hello! How can I help you today?'
            )
        ]
        
        for message in messages:
            db.session.add(message)
        
        db.session.commit()
        
        # Act
        retrieved_messages = ConversationRepository.get_messages(conversation.id)
        
        # Assert
        self.assertEqual(len(retrieved_messages), 2)
        self.assertEqual(retrieved_messages[0].role, 'user')
        self.assertEqual(retrieved_messages[1].role, 'assistant')
    
    def test_get_conversation_with_messages(self):
        """Test retrieving a conversation with all its messages."""
        # Arrange
        user_id = 'test_user'
        conversation = Conversation(
            user_id=user_id,
            title='Full Conversation',
            model='claude-3-opus-20240229'
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Add messages
        messages = [
            Message(
                conversation_id=conversation.id,
                role='user',
                content='What is the meaning of life?'
            ),
            Message(
                conversation_id=conversation.id,
                role='assistant',
                content='The meaning of life is a philosophical question that has been debated for centuries...'
            )
        ]
        
        for message in messages:
            db.session.add(message)
        
        db.session.commit()
        
        # Act
        result = ConversationRepository.get_conversation_with_messages(conversation.id)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result['conversation']['id'], conversation.id)
        self.assertEqual(len(result['messages']), 2)
        self.assertEqual(result['messages'][0]['role'], 'user')
        self.assertEqual(result['messages'][1]['role'], 'assistant')

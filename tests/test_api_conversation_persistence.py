"""
Unit tests for conversation persistence API endpoints.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from flask import Flask
from routes.api import api_bp


class TestConversationPersistenceAPI(unittest.TestCase):
    """Test cases for conversation persistence API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret'
        
        # Register the API blueprint
        self.app.register_blueprint(api_bp, url_prefix='/api')
        
        self.client = self.app.test_client()
        
        # Mock user for authentication
        self.mock_user = Mock()
        self.mock_user.id = "test_user_123"
        self.mock_user.is_authenticated = True
        
    def _mock_auth_decorators(self, mock_current_user):
        """Helper to mock authentication decorators."""
        mock_current_user.return_value = self.mock_user
        
        # Mock the decorators to pass through
        def mock_decorator(f):
            return f
            
        return mock_decorator
        
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    @patch('routes.api.ConversationManager')
    def test_list_conversations_with_pagination(self, mock_conv_manager_class, mock_check_domain, mock_login_required, mock_current_user):
        """Test listing conversations with pagination."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        mock_conv_manager = Mock()
        mock_conv_manager_class.return_value = mock_conv_manager
        
        # Mock conversation data
        mock_conversations = [
            {"id": 1, "title": "Conv 1", "message_count": 5},
            {"id": 2, "title": "Conv 2", "message_count": 3}
        ]
        mock_conv_manager.list_conversations.return_value = mock_conversations
        
        # Mock repository for total count
        with patch('routes.api.ConversationRepository') as mock_repo:
            mock_repo.get_conversations.return_value = [Mock(), Mock(), Mock()]  # 3 total
            
            # Test request
            response = self.client.get('/api/conversations?limit=2&offset=0&active_only=true')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            self.assertTrue(data['success'])
            self.assertEqual(len(data['conversations']), 2)
            self.assertEqual(data['pagination']['limit'], 2)
            self.assertEqual(data['pagination']['offset'], 0)
            self.assertEqual(data['pagination']['total'], 3)
            self.assertTrue(data['pagination']['has_more'])
            
            # Verify manager was called with correct parameters
            mock_conv_manager.list_conversations.assert_called_once_with(
                active_only=True, limit=2, offset=0
            )
            
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    @patch('routes.api.ConversationManager')
    def test_search_conversations(self, mock_conv_manager_class, mock_check_domain, mock_login_required, mock_current_user):
        """Test searching conversations."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        mock_conv_manager = Mock()
        mock_conv_manager_class.return_value = mock_conv_manager
        
        # Mock search results
        mock_results = [
            {"id": 1, "title": "Python development", "message_count": 10}
        ]
        mock_conv_manager.search_conversations.return_value = mock_results
        
        # Test request
        response = self.client.get('/api/conversations/search?q=python&limit=20')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['query'], 'python')
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['count'], 1)
        
        # Verify manager was called correctly
        mock_conv_manager.search_conversations.assert_called_once_with('python', 20)
        
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    def test_search_conversations_missing_query(self, mock_check_domain, mock_login_required, mock_current_user):
        """Test search endpoint with missing query parameter."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        # Test request without query
        response = self.client.get('/api/conversations/search')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertIn('Search query is required', data['error'])
        
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    @patch('routes.api.ConversationManager')
    @patch('routes.api.ConversationRepository')
    def test_create_conversation_with_persistence(self, mock_repo, mock_conv_manager_class, mock_check_domain, mock_login_required, mock_current_user):
        """Test creating a conversation with database persistence."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        mock_conv_manager = Mock()
        mock_conv_manager_class.return_value = mock_conv_manager
        mock_conv_manager.create_conversation.return_value = "123"
        
        mock_conversation = Mock()
        mock_conversation.to_dict.return_value = {
            "id": 123,
            "title": "Test Conversation",
            "model": "claude-3-haiku-20240307"
        }
        mock_repo.get_conversation.return_value = mock_conversation
        
        # Test request
        data = {
            "title": "Test Conversation",
            "model": "claude-3-haiku-20240307"
        }
        response = self.client.post('/api/conversations', 
                                  json=data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['conversation']['id'], 123)
        self.assertEqual(response_data['conversation']['title'], "Test Conversation")
        
        # Verify manager was called correctly
        mock_conv_manager.create_conversation.assert_called_once_with(
            title="Test Conversation",
            model="claude-3-haiku-20240307"
        )
        
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    @patch('routes.api.ConversationRepository')
    @patch('routes.api.ConversationManager')
    def test_update_conversation(self, mock_conv_manager_class, mock_repo, mock_check_domain, mock_login_required, mock_current_user):
        """Test updating conversation metadata."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        mock_conversation = Mock()
        mock_conversation.user_id = "test_user_123"
        mock_conversation.to_dict.return_value = {
            "id": 123,
            "title": "Updated Title",
            "is_active": True
        }
        mock_repo.get_conversation.return_value = mock_conversation
        
        mock_conv_manager = Mock()
        mock_conv_manager_class.return_value = mock_conv_manager
        mock_conv_manager.update_conversation.return_value = True
        
        # Test request
        data = {"title": "Updated Title"}
        response = self.client.put('/api/conversations/123',
                                 json=data,
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['conversation']['title'], "Updated Title")
        
        # Verify manager was called correctly
        mock_conv_manager.update_conversation.assert_called_once_with(
            conversation_id=123,
            title="Updated Title",
            is_active=None
        )
        
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    @patch('routes.api.ConversationRepository')
    def test_update_conversation_unauthorized(self, mock_repo, mock_check_domain, mock_login_required, mock_current_user):
        """Test updating conversation that doesn't belong to user."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        mock_conversation = Mock()
        mock_conversation.user_id = "other_user_456"  # Different user
        mock_repo.get_conversation.return_value = mock_conversation
        
        # Test request
        data = {"title": "Updated Title"}
        response = self.client.put('/api/conversations/123',
                                 json=data,
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertIn('Not authorized', data['error'])
        
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    @patch('routes.api.ConversationRepository')
    @patch('routes.api.ConversationManager')
    def test_delete_conversation_soft(self, mock_conv_manager_class, mock_repo, mock_check_domain, mock_login_required, mock_current_user):
        """Test soft deleting a conversation."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        mock_conversation = Mock()
        mock_conversation.user_id = "test_user_123"
        mock_repo.get_conversation.return_value = mock_conversation
        
        mock_conv_manager = Mock()
        mock_conv_manager_class.return_value = mock_conv_manager
        mock_conv_manager.delete_conversation.return_value = True
        
        # Test request (default is soft delete)
        response = self.client.delete('/api/conversations/123')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('deactivated', data['message'])
        
        # Verify manager was called correctly
        mock_conv_manager.delete_conversation.assert_called_once_with(123, soft_delete=True)
        
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    @patch('routes.api.ConversationRepository')
    @patch('routes.api.ConversationManager')
    def test_delete_conversation_hard(self, mock_conv_manager_class, mock_repo, mock_check_domain, mock_login_required, mock_current_user):
        """Test hard deleting a conversation."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        mock_conversation = Mock()
        mock_conversation.user_id = "test_user_123"
        mock_repo.get_conversation.return_value = mock_conversation
        
        mock_conv_manager = Mock()
        mock_conv_manager_class.return_value = mock_conv_manager
        mock_conv_manager.delete_conversation.return_value = True
        
        # Test request with hard delete
        response = self.client.delete('/api/conversations/123?soft_delete=false')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('deleted', data['message'])
        
        # Verify manager was called correctly
        mock_conv_manager.delete_conversation.assert_called_once_with(123, soft_delete=False)
        
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    @patch('routes.api.ConversationRepository')
    @patch('routes.api.ConversationManager')
    def test_bulk_delete_conversations(self, mock_conv_manager_class, mock_repo, mock_check_domain, mock_login_required, mock_current_user):
        """Test bulk deleting conversations."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        # Mock conversations that belong to user
        mock_conv1 = Mock()
        mock_conv1.user_id = "test_user_123"
        mock_conv2 = Mock()
        mock_conv2.user_id = "test_user_123"
        
        def mock_get_conversation(conv_id):
            if conv_id == 1:
                return mock_conv1
            elif conv_id == 2:
                return mock_conv2
            return None
            
        mock_repo.get_conversation.side_effect = mock_get_conversation
        
        mock_conv_manager = Mock()
        mock_conv_manager_class.return_value = mock_conv_manager
        mock_conv_manager.delete_conversation.return_value = True
        
        # Test request
        data = {
            "conversation_ids": [1, 2],
            "soft_delete": True
        }
        response = self.client.delete('/api/conversations/bulk',
                                    json=data,
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['summary']['total'], 2)
        self.assertEqual(response_data['summary']['successful'], 2)
        self.assertEqual(response_data['summary']['failed'], 0)
        
        # Verify all conversations were processed
        self.assertEqual(len(response_data['results']), 2)
        for result in response_data['results']:
            self.assertTrue(result['success'])
            
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    def test_bulk_delete_invalid_request(self, mock_check_domain, mock_login_required, mock_current_user):
        """Test bulk delete with invalid request data."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        # Test request with empty conversation_ids
        data = {"conversation_ids": []}
        response = self.client.delete('/api/conversations/bulk',
                                    json=data,
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertIn('non-empty list', data['error'])
        
    @patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123")))
    @patch('routes.api.login_required')
    @patch('routes.api.check_lynxx_domain')
    @patch('routes.api.ConversationManager')
    @patch('routes.api.anthropic_api')
    def test_send_prompt_with_persistence(self, mock_api, mock_conv_manager_class, mock_check_domain, mock_login_required, mock_current_user):
        """Test sending a prompt with conversation persistence."""
        # Setup mocks
        mock_login_required.side_effect = self._mock_auth_decorators(mock_current_user)
        mock_check_domain.side_effect = self._mock_auth_decorators(mock_current_user)
        
        mock_conv_manager = Mock()
        mock_conv_manager_class.return_value = mock_conv_manager
        
        # Mock API response
        mock_response = {
            "success": True,
            "message": "Hello! How can I help you?",
            "conversation_id": 123,
            "active_mcp_servers": []
        }
        mock_api.send_prompt.return_value = mock_response
        
        # Test request
        data = {
            "prompt": "Hello Claude!",
            "model_id": "claude-3-haiku-20240307"
        }
        response = self.client.post('/api/prompt',
                                  json=data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], "Hello! How can I help you?")
        self.assertEqual(response_data['conversation_id'], 123)
        
        # Verify that the conversation manager was temporarily set
        self.assertEqual(mock_api.send_prompt.call_count, 1)
        
    def test_pagination_parameter_validation(self):
        """Test validation of pagination parameters."""
        with patch('routes.api.current_user', new_callable=lambda: Mock(return_value=Mock(id="test_user_123"))):
            with patch('routes.api.login_required') as mock_login_required:
                with patch('routes.api.check_lynxx_domain') as mock_check_domain:
                    with patch('routes.api.ConversationManager') as mock_conv_manager_class:
                        with patch('routes.api.ConversationRepository') as mock_repo:
                            # Setup mocks
                            mock_login_required.return_value = lambda f: f
                            mock_check_domain.return_value = lambda f: f
                            
                            mock_conv_manager = Mock()
                            mock_conv_manager_class.return_value = mock_conv_manager
                            mock_conv_manager.list_conversations.return_value = []
                            
                            mock_repo.get_conversations.return_value = []
                            
                            # Test with limit > 100 (should be capped)
                            response = self.client.get('/api/conversations?limit=150')
                            self.assertEqual(response.status_code, 200)
                            
                            # Verify limit was capped at 100
                            args, kwargs = mock_conv_manager.list_conversations.call_args
                            self.assertEqual(kwargs['limit'], 100)
                            
                            # Test with negative offset (should be set to 0)
                            response = self.client.get('/api/conversations?offset=-5')
                            self.assertEqual(response.status_code, 200)
                            
                            # Verify offset was set to 0
                            args, kwargs = mock_conv_manager.list_conversations.call_args
                            self.assertEqual(kwargs['offset'], 0)


if __name__ == '__main__':
    unittest.main()
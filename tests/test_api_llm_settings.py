"""
API tests for LLM settings endpoints.
"""
import json
import pytest
from unittest.mock import patch, Mock
from flask import Flask
from flask_testing import TestCase
from routes.api import api_bp
from anthropic_api import AnthropicAPI


class TestLLMSettingsAPI(TestCase):
    """Test LLM settings API endpoints."""
    
    def create_app(self):
        """Create test app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.register_blueprint(api_bp, url_prefix='/api')
        return app
    
    def setUp(self):
        """Set up test environment."""
        # Mock authentication
        self.user_patcher = patch('routes.api.current_user')
        self.mock_user = self.user_patcher.start()
        self.mock_user.is_authenticated = True
        self.mock_user.id = 1
        
        # Mock domain check
        self.domain_patcher = patch('routes.api.check_lynxx_domain')
        self.mock_domain_check = self.domain_patcher.start()
        self.mock_domain_check.return_value = lambda f: f
        
        # Mock login required
        self.login_patcher = patch('routes.api.login_required')
        self.mock_login_required = self.login_patcher.start()
        self.mock_login_required.return_value = lambda f: f
        
        # Mock anthropic_api
        self.api_patcher = patch('routes.api.anthropic_api')
        self.mock_anthropic_api = self.api_patcher.start()
        
    def tearDown(self):
        """Clean up test environment."""
        self.user_patcher.stop()
        self.domain_patcher.stop()
        self.login_patcher.stop()
        self.api_patcher.stop()
    
    def test_get_llm_settings_default(self):
        """Test GET /api/llm-settings with default parameters."""
        self.mock_anthropic_api.get_llm_settings.return_value = {
            'temperature': 0.2,
            'max_tokens': 4000
        }
        
        response = self.client.get('/api/llm-settings')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('settings', data)
        self.assertEqual(data['settings']['temperature'], 0.2)
        self.assertEqual(data['settings']['max_tokens'], 4000)
        self.assertIsNone(data['model_id'])
        self.assertIsNone(data['preset_name'])
        
        self.mock_anthropic_api.get_llm_settings.assert_called_once_with(
            model_id=None, preset_name=None
        )
    
    def test_get_llm_settings_with_model(self):
        """Test GET /api/llm-settings with model_id parameter."""
        model_id = 'claude-3-opus-20240229'
        self.mock_anthropic_api.get_llm_settings.return_value = {
            'temperature': 0.1,
            'max_tokens': 4096
        }
        
        response = self.client.get(f'/api/llm-settings?model_id={model_id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['model_id'], model_id)
        self.mock_anthropic_api.get_llm_settings.assert_called_once_with(
            model_id=model_id, preset_name=None
        )
    
    def test_get_llm_settings_with_preset(self):
        """Test GET /api/llm-settings with preset_name parameter."""
        preset_name = 'creative_writing'
        self.mock_anthropic_api.get_llm_settings.return_value = {
            'temperature': 0.8,
            'max_tokens': 8000
        }
        
        response = self.client.get(f'/api/llm-settings?preset_name={preset_name}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['preset_name'], preset_name)
        self.mock_anthropic_api.get_llm_settings.assert_called_once_with(
            model_id=None, preset_name=preset_name
        )
    
    def test_get_llm_settings_error(self):
        """Test GET /api/llm-settings with API error."""
        self.mock_anthropic_api.get_llm_settings.side_effect = Exception('API Error')
        
        response = self.client.get('/api/llm-settings')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'API Error')
    
    def test_update_llm_settings_valid(self):
        """Test PUT /api/llm-settings with valid parameters."""
        self.mock_anthropic_api.update_runtime_settings.return_value = {
            'temperature': 0.5,
            'max_tokens': 6000
        }
        
        request_data = {
            'temperature': 0.5,
            'max_tokens': 6000
        }
        
        response = self.client.put(
            '/api/llm-settings',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('settings', data)
        self.assertEqual(data['settings']['temperature'], 0.5)
        self.assertEqual(data['settings']['max_tokens'], 6000)
        self.assertIn('message', data)
        
        self.mock_anthropic_api.update_runtime_settings.assert_called_once_with(
            temperature=0.5, max_tokens=6000
        )
    
    def test_update_llm_settings_partial(self):
        """Test PUT /api/llm-settings with only temperature."""
        self.mock_anthropic_api.update_runtime_settings.return_value = {
            'temperature': 0.8,
            'max_tokens': 4000
        }
        
        request_data = {'temperature': 0.8}
        
        response = self.client.put(
            '/api/llm-settings',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.mock_anthropic_api.update_runtime_settings.assert_called_once_with(
            temperature=0.8, max_tokens=None
        )
    
    def test_update_llm_settings_invalid_temperature(self):
        """Test PUT /api/llm-settings with invalid temperature."""
        request_data = {'temperature': 1.5}
        
        response = self.client.put(
            '/api/llm-settings',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertIn('Temperature must be between 0.0 and 1.0', data['error'])
        self.mock_anthropic_api.update_runtime_settings.assert_not_called()
    
    def test_update_llm_settings_invalid_max_tokens(self):
        """Test PUT /api/llm-settings with invalid max_tokens."""
        request_data = {'max_tokens': -100}
        
        response = self.client.put(
            '/api/llm-settings',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertIn('Max tokens must be greater than 0', data['error'])
        self.mock_anthropic_api.update_runtime_settings.assert_not_called()
    
    def test_update_llm_settings_validation_error(self):
        """Test PUT /api/llm-settings with validation error from API."""
        self.mock_anthropic_api.update_runtime_settings.side_effect = ValueError('Invalid settings')
        
        request_data = {'temperature': 0.5}
        
        response = self.client.put(
            '/api/llm-settings',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Invalid settings')
    
    def test_get_default_settings(self):
        """Test GET /api/llm-settings/defaults."""
        self.mock_anthropic_api.temperature = 0.2
        self.mock_anthropic_api.max_tokens = 4000
        self.mock_anthropic_api.default_model = 'claude-3-haiku-20240307'
        
        response = self.client.get('/api/llm-settings/defaults')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('defaults', data)
        defaults = data['defaults']
        self.assertEqual(defaults['temperature'], 0.2)
        self.assertEqual(defaults['max_tokens'], 4000)
        self.assertEqual(defaults['default_model'], 'claude-3-haiku-20240307')
    
    def test_get_presets(self):
        """Test GET /api/llm-settings/presets."""
        expected_presets = [
            {
                'id': 'developer_agent',
                'name': 'Python Developer Agent',
                'temperature': 0.2,
                'max_tokens': 4000,
                'description': 'Optimized for code generation'
            },
            {
                'id': 'creative_writing',
                'name': 'Creative Writing',
                'temperature': 0.8,
                'max_tokens': 8000,
                'description': 'Higher creativity for writing'
            }
        ]
        self.mock_anthropic_api.get_available_presets.return_value = expected_presets
        
        response = self.client.get('/api/llm-settings/presets')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('presets', data)
        self.assertEqual(data['presets'], expected_presets)
        self.mock_anthropic_api.get_available_presets.assert_called_once()
    
    def test_get_presets_error(self):
        """Test GET /api/llm-settings/presets with API error."""
        self.mock_anthropic_api.get_available_presets.side_effect = Exception('API Error')
        
        response = self.client.get('/api/llm-settings/presets')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'API Error')
    
    @patch('routes.api.ConversationManager')
    @patch('routes.api.ConversationRepository')
    def test_send_prompt_with_temperature(self, mock_repo, mock_conv_manager):
        """Test POST /api/prompt with temperature parameter."""
        # Setup mocks
        self.mock_anthropic_api.send_prompt.return_value = {
            'success': True,
            'message': 'Response',
            'temperature': 0.8,
            'max_tokens': 4000
        }
        
        request_data = {
            'prompt': 'Hello',
            'temperature': 0.8
        }
        
        response = self.client.post(
            '/api/prompt',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        
        # Verify temperature was passed to send_prompt
        call_args = self.mock_anthropic_api.send_prompt.call_args
        self.assertEqual(call_args[1]['temperature'], 0.8)
    
    @patch('routes.api.ConversationManager')
    @patch('routes.api.ConversationRepository')
    def test_send_prompt_with_preset(self, mock_repo, mock_conv_manager):
        """Test POST /api/prompt with preset_name parameter."""
        self.mock_anthropic_api.send_prompt.return_value = {
            'success': True,
            'message': 'Response',
            'preset_name': 'creative_writing'
        }
        
        request_data = {
            'prompt': 'Write a story',
            'preset_name': 'creative_writing'
        }
        
        response = self.client.post(
            '/api/prompt',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        
        # Verify preset_name was passed to send_prompt
        call_args = self.mock_anthropic_api.send_prompt.call_args
        self.assertEqual(call_args[1]['preset_name'], 'creative_writing')
    
    @patch('routes.api.ConversationManager')
    @patch('routes.api.ConversationRepository')
    def test_send_prompt_invalid_temperature(self, mock_repo, mock_conv_manager):
        """Test POST /api/prompt with invalid temperature."""
        request_data = {
            'prompt': 'Hello',
            'temperature': 2.0  # Invalid
        }
        
        response = self.client.post(
            '/api/prompt',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertIn('Temperature must be between 0.0 and 1.0', data['error'])
        self.mock_anthropic_api.send_prompt.assert_not_called()
    
    @patch('routes.api.ConversationManager')
    @patch('routes.api.ConversationRepository')
    def test_send_prompt_invalid_max_tokens(self, mock_repo, mock_conv_manager):
        """Test POST /api/prompt with invalid max_tokens."""
        request_data = {
            'prompt': 'Hello',
            'max_tokens': 0  # Invalid
        }
        
        response = self.client.post(
            '/api/prompt',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertIn('Max tokens must be greater than 0', data['error'])
        self.mock_anthropic_api.send_prompt.assert_not_called()
    
    def test_send_prompt_stream_with_temperature(self):
        """Test GET /api/prompt_stream with temperature parameter."""
        with patch('routes.api.threading') as mock_threading:
            with patch('routes.api.current_app') as mock_app:
                mock_app._get_current_object.return_value = self.app
                
                response = self.client.get(
                    '/api/prompt_stream?prompt=Hello&temperature=0.8'
                )
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, 'text/event-stream')
                
                # Verify threading was called (stream started)
                mock_threading.Thread.assert_called_once()
    
    def test_send_prompt_stream_invalid_temperature(self):
        """Test GET /api/prompt_stream with invalid temperature."""
        response = self.client.get(
            '/api/prompt_stream?prompt=Hello&temperature=2.0'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertFalse(data['success'])
        self.assertIn('Temperature must be between 0.0 and 1.0', data['error'])


if __name__ == '__main__':
    import unittest
    unittest.main()
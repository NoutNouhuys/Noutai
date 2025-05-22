import unittest
from unittest.mock import patch, MagicMock
import os

from anthropic_api import AnthropicAPI

class TestPromptCacheControl(unittest.TestCase):
    def setUp(self):
        os.environ['ANTHROPIC_API_KEY'] = 'test-key'

    def tearDown(self):
        os.environ.pop('ANTHROPIC_API_KEY', None)

    @patch('anthropic.Anthropic')
    def test_cache_control_added(self, mock_anthropic):
        mock_client = MagicMock()
        response_obj = MagicMock()
        content = MagicMock()
        content.text = 'hi'
        response_obj.content = [content]
        response_obj.stop_reason = None
        mock_client.messages.create.return_value = response_obj
        mock_anthropic.return_value = mock_client

        api = AnthropicAPI(api_key='test-key')
        conv_id = api.create_conversation()
        api.add_to_conversation(conv_id, 'Hello', 'Hi there')

        api.send_prompt('Next', conversation_id=conv_id, include_logs=False)

        messages = mock_client.messages.create.call_args[1]['messages']
        self.assertIn('cache_control', messages[-2])
        self.assertEqual(messages[-2]['cache_control']['ttl'], '5m')

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import os

from cache_manager import read_from_cache, clear_cache
from anthropic_api import AnthropicAPI


class TestCacheIntegration(unittest.TestCase):
    def setUp(self):
        os.environ['ANTHROPIC_API_KEY'] = 'test-key'
        os.environ['MCP_SERVER_SCRIPT'] = 'script.py'
        clear_cache()

    def tearDown(self):
        clear_cache()
        os.environ.pop('ANTHROPIC_API_KEY', None)
        os.environ.pop('MCP_SERVER_SCRIPT', None)

    def test_load_werkwijze_cached(self):
        api = AnthropicAPI(api_key='test-key')
        self.assertIsNotNone(read_from_cache('werkwijze'))

    @patch('mcp_connector.MCPConnector.connect_to_server', new_callable=AsyncMock)
    @patch('mcp_connector.MCPConnector.get_tools', new_callable=AsyncMock)
    @patch('anthropic.Anthropic')
    def test_mcp_tools_cached(self, mock_anthropic, mock_get_tools, mock_connect):
        mock_client = MagicMock()
        response_obj = MagicMock()
        content = MagicMock()
        content.text = 'hi'
        response_obj.content = [content]
        response_obj.stop_reason = None
        mock_client.messages.create.return_value = response_obj
        mock_anthropic.return_value = mock_client

        mock_get_tools.return_value = [{"name": "tool1", "description": "", "input_schema": {}}]

        api = AnthropicAPI(api_key='test-key')

        api.send_prompt('prompt', include_logs=False)
        self.assertEqual(mock_get_tools.call_count, 1)

        api.send_prompt('prompt', include_logs=False)
        self.assertEqual(mock_get_tools.call_count, 1)


if __name__ == '__main__':
    unittest.main()

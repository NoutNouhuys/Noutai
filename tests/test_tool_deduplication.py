import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from anthropic_api import AnthropicAPI


class TestToolDeduplication(unittest.TestCase):
    def setUp(self):
        os.environ['ANTHROPIC_API_KEY'] = 'test-key'
        os.environ['MCP_SERVER_SCRIPT'] = 'script.py'

    def tearDown(self):
        os.environ.pop('MCP_SERVER_SCRIPT', None)
        os.environ.pop('ANTHROPIC_API_KEY', None)

    @patch('mcp_connector.MCPConnector.connect_to_server', new_callable=AsyncMock)
    @patch('mcp_connector.MCPConnector.get_tools', new_callable=AsyncMock)
    @patch('anthropic.Anthropic')
    def test_send_prompt_deduplicates_tools(self, mock_anthropic, mock_get_tools, mock_connect):
        mock_client = MagicMock()
        response_obj = MagicMock()
        content = MagicMock()
        content.text = 'hi'
        response_obj.content = [content]
        response_obj.stop_reason = None
        mock_client.messages.create.return_value = response_obj
        mock_anthropic.return_value = mock_client

        mock_get_tools.return_value = [
            {"name": "tool1", "description": "", "input_schema": {}},
            {"name": "tool1", "description": "", "input_schema": {}},
        ]

        api = AnthropicAPI(api_key='test-key')
        api.send_prompt('prompt', include_logs=False)

        called_tools = mock_client.messages.create.call_args[1]['tools']
        names = [t['name'] for t in called_tools]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn('get_werkwijze', names)
        self.assertIn('tool1', names)


if __name__ == '__main__':
    unittest.main()

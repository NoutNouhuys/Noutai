import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil

from anthropic_api import AnthropicAPI


class TestWerkwijzeRepo(unittest.TestCase):
    """Verify repo werkwijze is injected into prompts."""

    @patch('anthropic.Anthropic')
    def test_repo_path_inserts_werkwijze(self, mock_anthropic):
        mock_client = MagicMock()
        resp_content = MagicMock()
        resp_content.text = 'ok'
        resp = MagicMock()
        resp.content = [resp_content]
        resp.stop_reason = None
        mock_client.messages.create.return_value = resp
        mock_anthropic.return_value = mock_client

        api = AnthropicAPI(api_key='test-key')
        api.werkwijze = 'instructies'

        api.send_prompt('vraag', include_logs=False)

        params = mock_client.messages.create.call_args[1]
        self.assertIn('system', params)
        self.assertIn('instructies', params['system'])


if __name__ == '__main__':
    unittest.main()

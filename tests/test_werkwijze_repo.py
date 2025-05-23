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

        temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(temp_dir, 'werkwijze'), exist_ok=True)
        werkwijze_file = os.path.join(temp_dir, 'werkwijze', 'werkwijze.txt')
        with open(werkwijze_file, 'w', encoding='utf-8') as f:
            f.write('instructies')

        try:
            api.send_prompt('vraag', repo_path=temp_dir, include_logs=False)
        finally:
            shutil.rmtree(temp_dir)

        messages = mock_client.messages.create.call_args[1]['messages']
        self.assertEqual(messages[-2]['role'], 'system')
        self.assertEqual(messages[-2]['content'], 'instructies')
        self.assertIn('cache_control', messages[-2])
        self.assertEqual(messages[-2]['cache_control']['ttl'], '5m')


if __name__ == '__main__':
    unittest.main()

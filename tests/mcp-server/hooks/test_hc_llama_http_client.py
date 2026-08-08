"""
solid-description: Validates HTTP chat client request handling, response parsing, and error resilience.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from hc_llama_runner import LlamaHttpClient, TOOLS  # noqa: E402


def _urlopen_mock(body: dict):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(body).encode()
    return cm


def _no_tool_response(content: str) -> dict:
    return {"choices": [{"finish_reason": "stop",
                         "message": {"role": "assistant", "content": content, "tool_calls": []}}]}


class TestLlamaHttpClient(unittest.TestCase):
    def setUp(self):
        self.client = LlamaHttpClient(host="http://localhost:8080", model="local")

    def test_returns_parsed_response_on_success(self):
        body = _no_tool_response("ok")
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(body)):
            result = self.client.chat([{"role": "user", "content": "hi"}], TOOLS, 30)
        self.assertEqual(result, body)

    def test_returns_none_on_connection_error(self):
        with patch("urllib.request.urlopen", side_effect=OSError("refused")):
            self.assertIsNone(self.client.chat([], TOOLS, 30))

    def test_returns_none_on_json_decode_error(self):
        cm = MagicMock()
        cm.__enter__.return_value.read.return_value = b"not json"
        with patch("urllib.request.urlopen", return_value=cm):
            self.assertIsNone(self.client.chat([], TOOLS, 30))

    def test_posts_to_v1_chat_completions(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return _urlopen_mock(_no_tool_response("x"))
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.chat([], TOOLS, 30)
        self.assertIn("/v1/chat/completions", captured[0])

    def test_includes_tools_in_request_body(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(json.loads(req.data))
            return _urlopen_mock(_no_tool_response("x"))
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.chat([], TOOLS, 30)
        self.assertEqual(len(captured[0]["tools"]), len(TOOLS))


if __name__ == "__main__":
    unittest.main()

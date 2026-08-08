"""
solid-description: Validates the separation and formatting of thinking content from model responses.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from hc_llama_runner import _strip_thinking  # noqa: E402


class TestStripThinking(unittest.TestCase):
    def test_returns_empty_thinking_and_content_unchanged_when_no_think_block(self):
        thinking, response = _strip_thinking('{"violations": []}')
        self.assertEqual(thinking, "")
        self.assertEqual(response, '{"violations": []}')

    def test_strips_think_block_and_returns_both_parts(self):
        raw = "<think>reasoning here</think>\n\n{\"violations\": []}"
        thinking, response = _strip_thinking(raw)
        self.assertEqual(thinking, "reasoning here")
        self.assertEqual(response, '{"violations": []}')

    def test_trims_whitespace_from_thinking_and_response(self):
        raw = "<think>  reasoning  </think>   {\"violations\": []}"
        thinking, response = _strip_thinking(raw)
        self.assertEqual(thinking, "reasoning")
        self.assertEqual(response, '{"violations": []}')

    def test_multiline_thinking_block(self):
        raw = "<think>\nStep 1: check SRP\nStep 2: check OCP\n</think>\n\n{\"violations\": []}"
        thinking, response = _strip_thinking(raw)
        self.assertIn("Step 1", thinking)
        self.assertIn("Step 2", thinking)
        self.assertEqual(response, '{"violations": []}')

    def test_empty_think_block_returns_empty_thinking(self):
        raw = "<think>\n\n</think>\n\n{\"violations\": []}"
        thinking, response = _strip_thinking(raw)
        self.assertEqual(thinking, "")
        self.assertEqual(response, '{"violations": []}')

    def test_empty_string_returns_empty_pair(self):
        thinking, response = _strip_thinking("")
        self.assertEqual(thinking, "")
        self.assertEqual(response, "")

    def test_content_without_json_returned_intact(self):
        thinking, response = _strip_thinking("plain text response")
        self.assertEqual(thinking, "")
        self.assertEqual(response, "plain text response")


if __name__ == "__main__":
    unittest.main()

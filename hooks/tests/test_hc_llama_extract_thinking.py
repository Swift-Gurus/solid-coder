"""
solid-description: Verifies correct extraction of model reasoning from messages.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_llama_runner import _extract_thinking_and_content  # noqa: E402


class TestExtractThinkingAndContent(unittest.TestCase):
    def test_returns_reasoning_content_field_when_present(self):
        msg = {"reasoning_content": "model reasoning here", "content": "final answer"}
        thinking, content = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "model reasoning here")
        self.assertEqual(content, "final answer")

    def test_falls_back_to_think_tag_stripping_when_no_reasoning_content(self):
        msg = {"content": "<think>inline reasoning</think>\nfinal answer"}
        thinking, content = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "inline reasoning")

    def test_prefers_reasoning_content_over_think_tags(self):
        msg = {"reasoning_content": "from field", "content": "<think>from tag</think>answer"}
        thinking, _ = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "from field")

    def test_returns_empty_thinking_when_neither_source_present(self):
        msg = {"content": "plain answer"}
        thinking, content = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "")
        self.assertEqual(content, "plain answer")

    def test_handles_empty_message(self):
        thinking, content = _extract_thinking_and_content({})
        self.assertEqual(thinking, "")
        self.assertEqual(content, "")

    def test_strips_whitespace_from_reasoning_content(self):
        msg = {"reasoning_content": "  padded reasoning  ", "content": "answer"}
        thinking, _ = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "padded reasoning")


if __name__ == "__main__":
    unittest.main()

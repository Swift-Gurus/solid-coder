"""
solid-description: Unit tests for the LLM runner factory — config-file/env routing between Claude and local backends.
solid-category: unit-test
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_checker import ClaudeRunner
from hc_llama_runner import LlamaServerRunner
from hc_runner_factory import make_llm_runner


class TestMakeLlmRunner(unittest.TestCase):
    def _kwargs_for_local_backend(self, backend="local", host=None, model=None) -> dict:
        with patch("hc_runner_factory.make_llama_server_runner") as mock_make, \
             patch("hc_runner_factory.llm_backend", return_value=backend), \
             patch("hc_runner_factory.llm_host", return_value=host or "http://localhost:8080"), \
             patch("hc_runner_factory.llm_model", return_value=model or "local"):
            mock_make.return_value = MagicMock(spec=LlamaServerRunner)
            make_llm_runner("config", "tools")
            _, kwargs = mock_make.call_args
        return kwargs

    def test_returns_claude_runner_when_backend_is_claude(self):
        with patch("hc_runner_factory.llm_backend", return_value="claude"):
            runner = make_llm_runner("config", "tools")
        self.assertIsInstance(runner, ClaudeRunner)

    def test_returns_llama_runner_when_backend_is_local(self):
        with patch("hc_runner_factory.llm_backend", return_value="local"), \
             patch("hc_runner_factory.llm_host", return_value="http://localhost:8080"), \
             patch("hc_runner_factory.llm_model", return_value="local"):
            runner = make_llm_runner("config", "tools")
        self.assertIsInstance(runner, LlamaServerRunner)

    def test_backend_matching_is_case_insensitive(self):
        with patch("hc_runner_factory.llm_backend", return_value="LOCAL"), \
             patch("hc_runner_factory.llm_host", return_value="http://localhost:8080"), \
             patch("hc_runner_factory.llm_model", return_value="local"):
            runner = make_llm_runner("config", "tools")
        self.assertIsInstance(runner, LlamaServerRunner)

    def test_local_backend_passes_resolved_host(self):
        kwargs = self._kwargs_for_local_backend(host="http://myhost:9999")
        self.assertEqual(kwargs["host"], "http://myhost:9999")

    def test_local_backend_passes_resolved_model(self):
        kwargs = self._kwargs_for_local_backend(model="qwen3-35b")
        self.assertEqual(kwargs["model"], "qwen3-35b")

    def test_local_backend_uses_default_host(self):
        kwargs = self._kwargs_for_local_backend()
        self.assertEqual(kwargs["host"], "http://localhost:8080")


if __name__ == "__main__":
    unittest.main()

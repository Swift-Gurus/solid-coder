"""
solid-description: Validates LLM runner factory backend selection and parameter handling.
solid-category: unit-test
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_checker import ClaudeRunner  # noqa: E402
from hc_llama_runner import LlamaServerRunner  # noqa: E402
from hc_runner_factory import make_llm_runner  # noqa: E402


class TestMakeLlmRunner(unittest.TestCase):
    def _kwargs_for_local_backend(self, backend="local", host=None, model=None) -> dict:
        with patch("hc_llama_runner.make_llama_server_runner") as mock_make, \
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

    def test_claude_backend_forwards_real_model_id(self):
        with patch("hc_runner_factory.llm_backend", return_value="claude"), \
             patch("hc_runner_factory.llm_model", return_value="claude-haiku-4-5"):
            runner = make_llm_runner("config", "tools")
        self.assertIsInstance(runner, ClaudeRunner)
        self.assertEqual(runner._model, "claude-haiku-4-5")

    def test_claude_backend_omits_model_for_placeholder_claude(self):
        with patch("hc_runner_factory.llm_backend", return_value="claude"), \
             patch("hc_runner_factory.llm_model", return_value="claude"):
            runner = make_llm_runner("config", "tools")
        self.assertEqual(runner._model, "")

    def test_claude_backend_omits_model_for_placeholder_local(self):
        with patch("hc_runner_factory.llm_backend", return_value="claude"), \
             patch("hc_runner_factory.llm_model", return_value="local"):
            runner = make_llm_runner("config", "tools")
        self.assertEqual(runner._model, "")

    def test_claude_backend_omits_model_when_empty(self):
        with patch("hc_runner_factory.llm_backend", return_value="claude"), \
             patch("hc_runner_factory.llm_model", return_value=""):
            runner = make_llm_runner("config", "tools")
        self.assertEqual(runner._model, "")


if __name__ == "__main__":
    unittest.main()

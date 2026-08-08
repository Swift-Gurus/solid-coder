"""
solid-description: Validates TOML configuration for LLM backend selection and initialization.
solid-category: unit-test
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from hc_checker import ClaudeRunner  # noqa: E402
from hc_llama_runner import LlamaServerRunner  # noqa: E402
from hc_runner_factory import make_llm_runner  # noqa: E402
from test_utils import write_toml  # noqa: E402


class TestTomlIntegration(unittest.TestCase):
    """Integration tests: full path from TOML file → runner configuration."""

    def _make_runner(self, tmp_path: Path, mcp_config: str = "cfg", allowed_tools: str = "tools"):
        from solid_coder_paths import CONFIG_DIR, CONFIG_LOCAL_TOML
        with patch("hc_config_core.find_config", return_value=tmp_path / CONFIG_DIR / CONFIG_LOCAL_TOML), \
             patch("local_runner_strategy.make_llama_server_runner") as mock_llama:
            mock_llama.return_value = MagicMock(spec=LlamaServerRunner)
            runner = make_llm_runner(mcp_config, allowed_tools)
            return runner, mock_llama

    def test_claude_backend_in_toml_creates_claude_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"claude\"\n")
            runner, _ = self._make_runner(tmp_path)
        self.assertIsInstance(runner, ClaudeRunner)

    def test_claude_model_in_toml_forwarded_to_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"claude\"\nmodel = \"claude-sonnet-4-5\"\n")
            runner, _ = self._make_runner(tmp_path)
        self.assertIsInstance(runner, ClaudeRunner)
        self.assertEqual(runner._model, "claude-sonnet-4-5")

    def test_local_backend_in_toml_creates_llama_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"local\"\nhost = \"http://localhost:8080\"\nmodel = \"qwen3-35b\"\n")
            _, mock_llama = self._make_runner(tmp_path)
        mock_llama.assert_called_once()
        kwargs = mock_llama.call_args[1]
        self.assertEqual(kwargs["host"], "http://localhost:8080")
        self.assertEqual(kwargs["model"], "qwen3-35b")

    def test_local_backend_passes_all_toml_args(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"local\"\nhost = \"http://myhost:9999\"\nmodel = \"my-model\"\n")
            _, mock_llama = self._make_runner(tmp_path)
        kwargs = mock_llama.call_args[1]
        self.assertEqual(kwargs["host"], "http://myhost:9999")
        self.assertEqual(kwargs["model"], "my-model")

    def test_placeholder_model_in_toml_not_forwarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"claude\"\nmodel = \"claude\"\n")
            runner, _ = self._make_runner(tmp_path)
        self.assertEqual(runner._model, "")


if __name__ == "__main__":
    unittest.main()

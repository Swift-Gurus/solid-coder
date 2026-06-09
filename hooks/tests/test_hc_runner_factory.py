"""
solid-description: Validates LLM backend selection and configuration parameter forwarding from settings.
solid-category: unit-test
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_checker import ClaudeRunner
from hc_llama_runner import LlamaServerRunner
from hc_runner_factory import make_llm_runner
from test_utils import write_toml
import hook_utils


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


class _CaptureRunner:
    """Test double: captures the cmd passed to SubprocessJsonRunner.run()."""

    def __init__(self, return_value):
        self.captured_cmd = None
        self._return_value = return_value

    def run(self, cmd, timeout=None, stdin=None):
        self.captured_cmd = cmd
        return self._return_value


class TestRunClaudeBareModel(unittest.TestCase):
    def _captured_cmd(self, **kwargs):
        """Return the cmd list passed to subprocess when run_claude_bare is called."""
        capture = _CaptureRunner([{"type": "result", "result": "ok"}])
        hook_utils.run_claude_bare("hello", runner=capture, **kwargs)
        return capture.captured_cmd

    def test_no_model_arg_when_model_is_empty(self):
        cmd = self._captured_cmd(model="")
        self.assertNotIn("--model", cmd)

    def test_model_arg_appended_when_set(self):
        cmd = self._captured_cmd(model="claude-haiku-4-5")
        self.assertIn("--model", cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], "claude-haiku-4-5")

    def test_model_appears_before_session_id(self):
        cmd = self._captured_cmd(model="claude-haiku-4-5", session_id="s123")
        self.assertLess(cmd.index("--model"), cmd.index("--session-id"))


class TestClaudeRunnerModel(unittest.TestCase):
    def _run_and_capture(self, model: str):
        captured = {}
        def fake_run_bare(prompt, **kwargs):
            captured.update(kwargs)
            return "ok"
        runner = ClaudeRunner(mcp_config="cfg", allowed_tools="tools", model=model, fn=fake_run_bare)
        runner.run("prompt", timeout=30)
        return captured

    def test_model_forwarded_to_run_bare(self):
        kw = self._run_and_capture("claude-haiku-4-5")
        self.assertEqual(kw.get("model"), "claude-haiku-4-5")

    def test_empty_model_forwarded_as_empty(self):
        kw = self._run_and_capture("")
        self.assertEqual(kw.get("model"), "")


class TestTomlIntegration(unittest.TestCase):
    """Integration tests: full path from TOML file → runner configuration."""

    def _make_runner(self, tmp_path: Path, mcp_config: str = "cfg", allowed_tools: str = "tools"):
        with patch("hc_config_core.find_config", return_value=tmp_path / ".claude" / "solid-coder-local.toml"), \
             patch("hc_runner_factory.make_llama_server_runner") as mock_llama:
            mock_llama.return_value = MagicMock(spec=LlamaServerRunner)
            runner = make_llm_runner(mcp_config, allowed_tools)
            return runner, mock_llama

    def test_claude_backend_in_toml_creates_claude_runner(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"claude\"\n")
            runner, _ = self._make_runner(tmp_path)
        self.assertIsInstance(runner, ClaudeRunner)

    def test_claude_model_in_toml_forwarded_to_runner(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"claude\"\nmodel = \"claude-sonnet-4-5\"\n")
            runner, _ = self._make_runner(tmp_path)
        self.assertIsInstance(runner, ClaudeRunner)
        self.assertEqual(runner._model, "claude-sonnet-4-5")

    def test_local_backend_in_toml_creates_llama_runner(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"local\"\nhost = \"http://localhost:8080\"\nmodel = \"qwen3-35b\"\n")
            _, mock_llama = self._make_runner(tmp_path)
        mock_llama.assert_called_once()
        kwargs = mock_llama.call_args[1]
        self.assertEqual(kwargs["host"], "http://localhost:8080")
        self.assertEqual(kwargs["model"], "qwen3-35b")

    def test_local_backend_passes_all_toml_args(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"local\"\nhost = \"http://myhost:9999\"\nmodel = \"my-model\"\n")
            _, mock_llama = self._make_runner(tmp_path)
        kwargs = mock_llama.call_args[1]
        self.assertEqual(kwargs["host"], "http://myhost:9999")
        self.assertEqual(kwargs["model"], "my-model")

    def test_placeholder_model_in_toml_not_forwarded(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, "[llm]\nbackend = \"claude\"\nmodel = \"claude\"\n")
            runner, _ = self._make_runner(tmp_path)
        self.assertEqual(runner._model, "")


class TestBareSessionTimeout(unittest.TestCase):
    """Verify bare_session_timeout reads from TOML and defaults correctly."""

    def test_default_is_300(self):
        from hc_config import bare_session_timeout
        with patch("hc_config_core.read_llm_section", return_value={}):
            self.assertEqual(bare_session_timeout(), 300)

    def test_reads_value_from_toml(self):
        from hc_config import bare_session_timeout
        with patch("hc_config_core.read_llm_section", return_value={"bare_session_timeout": 120}):
            self.assertEqual(bare_session_timeout(), 120)

    def test_falls_back_to_default_on_invalid_value(self):
        from hc_config import bare_session_timeout
        with patch("hc_config_core.read_llm_section", return_value={"bare_session_timeout": "not-a-number"}):
            self.assertEqual(bare_session_timeout(), 300)


if __name__ == "__main__":
    unittest.main()

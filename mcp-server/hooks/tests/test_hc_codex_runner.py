"""
solid-description: Verifies profile configuration, command generation, subprocess execution, and error handling for the LLM runner.
solid-category: unit-test
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from codex_command_builder import CodexCommandBuilder  # noqa: E402
from codex_profile_manager import CodexProfileManager  # noqa: E402
from codex_temp_file_manager import CodexTempFileManager  # noqa: E402
from hc_codex_runner import CodexRunner, make_codex_runner  # noqa: E402
from hook_utils import SubprocessError  # noqa: E402
from test_utils import TempDirTestBase  # noqa: E402


def _make_cmd_builder(model: str = "o4-mini", profile: str = "solid-coder-health"):
    return CodexCommandBuilder(model=model, profile_name=profile)


def _make_subprocess_mock(result_text: str, returncode: bool = True):
    mock = MagicMock()

    def side_effect(cmd, timeout=None, stdin=None, cwd=None):
        idx = cmd.index("--output-last-message") + 1
        Path(cmd[idx]).write_text(result_text, encoding="utf-8")
        return returncode, "", ""

    mock.run.side_effect = side_effect
    return mock


class _CodexRunnerTestBase(TempDirTestBase):
    def _runner(self, model: str = "o4-mini", subprocess_runner=None) -> CodexRunner:
        return CodexRunner(
            cmd_builder=_make_cmd_builder(model=model),
            temp_files=CodexTempFileManager(),
            subprocess_runner=subprocess_runner or MagicMock(run=MagicMock(return_value=(True, "", ""))),
        )

    def _runner_with_result(self, text: str) -> tuple:
        mock = _make_subprocess_mock(text)
        return self._runner(subprocess_runner=mock), mock


class TestCodexProfileManager(_CodexRunnerTestBase):
    """CodexProfileManager writes the profile file with absolute MCP server paths."""

    def test_profile_file_created(self):
        CodexProfileManager(codex_home=str(self.output_dir)).ensure_profile()
        self.assertTrue((self.output_dir / "solid-coder-health.config.toml").exists())

    def test_profile_contains_pipeline_and_docs(self):
        CodexProfileManager(codex_home=str(self.output_dir)).ensure_profile()
        content = (self.output_dir / "solid-coder-health.config.toml").read_text()
        self.assertIn("[mcp_servers.pipeline]", content)
        self.assertIn("[mcp_servers.docs]", content)

    def test_ensure_profile_returns_profile_name(self):
        name = CodexProfileManager(codex_home=str(self.output_dir)).ensure_profile()
        self.assertEqual(name, "solid-coder-health")

    def test_server_paths_are_absolute(self):
        CodexProfileManager(codex_home=str(self.output_dir)).ensure_profile()
        content = (self.output_dir / "solid-coder-health.config.toml").read_text()
        for line in content.splitlines():
            if line.strip().startswith('args = ["'):
                path = line.split('"')[1]
                self.assertTrue(Path(path).is_absolute(), f"path not absolute: {path}")


class TestCodexCommandBuilder(_CodexRunnerTestBase):
    """CodexCommandBuilder builds the correct CLI command."""

    def test_includes_model_flag(self):
        builder = CodexCommandBuilder(model="o3", profile_name="p")
        cmd = builder.build(Path("/tmp/result.txt"))
        self.assertIn("--model", cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], "o3")

    def test_includes_profile_flag(self):
        builder = CodexCommandBuilder(model="", profile_name="my-profile")
        cmd = builder.build(Path("/tmp/result.txt"))
        self.assertIn("--profile", cmd)
        self.assertEqual(cmd[cmd.index("--profile") + 1], "my-profile")

    def test_includes_output_last_message(self):
        builder = CodexCommandBuilder(model="", profile_name="p")
        cmd = builder.build(Path("/tmp/out.txt"))
        self.assertIn("--output-last-message", cmd)
        self.assertEqual(cmd[cmd.index("--output-last-message") + 1], "/tmp/out.txt")

    def test_omits_model_when_empty(self):
        builder = CodexCommandBuilder(model="", profile_name="p")
        cmd = builder.build(Path("/tmp/result.txt"))
        self.assertNotIn("--model", cmd)


class TestCodexRunnerRun(_CodexRunnerTestBase):
    """CodexRunner.run() returns the last message and handles errors."""

    def test_run_returns_last_message(self):
        runner, _ = self._runner_with_result("Findings submitted.")
        self.assertEqual(runner.run("prompt", timeout=30), "Findings submitted.")

    def test_run_passes_prompt_via_stdin_file(self):
        stdin_content = []

        def capture(cmd, timeout=None, stdin=None, cwd=None):
            stdin_content.append(stdin.read() if hasattr(stdin, "read") else stdin)
            idx = cmd.index("--output-last-message") + 1
            Path(cmd[idx]).write_text("ok", encoding="utf-8")
            return True, "", ""

        mock = MagicMock()
        mock.run.side_effect = capture
        runner = self._runner(subprocess_runner=mock)
        runner.run("my prompt text", timeout=30)
        self.assertEqual(stdin_content[0], "my prompt text")

    def test_run_raises_on_nonzero_exit(self):
        mock = MagicMock()
        mock.run.return_value = (False, "", "crashed")
        runner = self._runner(subprocess_runner=mock)
        with self.assertRaises(SubprocessError):
            runner.run("prompt", timeout=30)


class TestMakeCodexRunner(_CodexRunnerTestBase):
    """make_codex_runner() returns a CodexRunner and writes the profile."""

    def test_returns_codex_runner(self):
        self.assertIsInstance(make_codex_runner(codex_home=str(self.output_dir)), CodexRunner)

    def test_profile_written_on_construction(self):
        make_codex_runner(codex_home=str(self.output_dir))
        self.assertTrue((self.output_dir / "solid-coder-health.config.toml").exists())

    def test_factory_returns_codex_runner_for_codex_backend(self):
        from hc_runner_factory import make_llm_runner
        with (
            patch("hc_runner_factory.llm_backend", return_value="codex"),
            patch("hc_runner_factory.llm_model", return_value="o4-mini"),
            patch("hc_runner_factory.bare_session_timeout", return_value=300),
            patch("hc_runner_factory.codex_home", return_value=str(self.output_dir)),
        ):
            runner = make_llm_runner(mcp_config="", allowed_tools="")
        self.assertIsInstance(runner, CodexRunner)

    def test_codex_home_accessor_reads_from_config(self):
        from hc_config_llm import codex_home
        with patch("hc_config_llm.llm_value", return_value="/tmp/my-codex"):
            self.assertEqual(codex_home(), "/tmp/my-codex")


if __name__ == "__main__":
    unittest.main()

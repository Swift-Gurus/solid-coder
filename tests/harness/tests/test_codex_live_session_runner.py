"""Verifies conversion of Codex CLI events into a typed live-session result."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from codex_live_session_runner import CodexLiveSessionRunner  # noqa: E402
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_session_request import LiveSessionRequest  # noqa: E402
from live_session_result import LiveSessionResult  # noqa: E402


class TestCodexLiveSessionRunner(unittest.TestCase):

    def test_returns_child_thread_id_and_final_output(self) -> None:
        runner = CodexLiveSessionRunner()
        event_stream = '{"type":"thread.started","thread_id":"codex-child"}\n'

        result = self._run_with_output(runner, event_stream, "completed")

        self.assertEqual(result.session_id, "codex-child")
        self.assertEqual(result.final_output, "completed")

    def test_preserves_raw_command_output(self) -> None:
        runner = CodexLiveSessionRunner()
        completed = CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"type":"thread.started","thread_id":"codex-child"}\n',
            stderr="diagnostic",
        )
        with tempfile.TemporaryDirectory() as directory:
            artifact_directory = Path(directory)
            with patch(
                "codex_live_session_runner.subprocess.run",
                return_value=completed,
            ):
                event_stream = runner._execute(
                    self._request(),
                    {},
                    artifact_directory / "last-message.txt",
                    artifact_directory,
                )

            self.assertEqual(event_stream, completed.stdout)
            self.assertEqual(
                (artifact_directory / "codex-events.jsonl").read_text(),
                completed.stdout,
            )
            self.assertEqual(
                (artifact_directory / "codex-stderr.log").read_text(),
                completed.stderr,
            )

    def test_rejects_event_stream_without_child_thread_id(self) -> None:
        runner = CodexLiveSessionRunner()

        with self.assertRaisesRegex(RuntimeError, "no child thread ID"):
            self._run_with_output(runner, '{"type":"turn.started"}\n', "completed")

    def _run_with_output(
        self,
        runner: CodexLiveSessionRunner,
        event_stream: str,
        final_output: str,
    ) -> LiveSessionResult:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_home = root / "codex-home"
            codex_home.mkdir()
            sessions = codex_home / "sessions"
            sessions.mkdir()
            (sessions / "rollout.jsonl").write_text(event_stream, encoding="utf-8")
            (codex_home / "state_test.sqlite").write_text("state", encoding="utf-8")
            artifact_directory = root / "artifacts"
            artifact_directory.mkdir()
            result_path = artifact_directory / "last-message.txt"
            result_path.write_text(final_output, encoding="utf-8")
            with (
                patch(
                    "codex_live_session_runner.tempfile.mkdtemp",
                    return_value=str(codex_home),
                ),
                patch(
                    "codex_live_session_runner.LiveSessionArtifactDirectoryCreator.create",
                    return_value=artifact_directory,
                ),
                patch.object(runner, "_write_config"),
                patch.object(runner, "_link_auth"),
                patch.object(runner, "_install_plugin"),
                patch.object(runner, "_execute", return_value=event_stream),
            ):
                result = runner.run(self._request())

            self.assertEqual(result.artifact_directory, artifact_directory)
            self.assertTrue(
                (artifact_directory / "codex-runtime" / "sessions" / "rollout.jsonl").exists()
            )
            self.assertTrue(
                (artifact_directory / "codex-runtime" / "state_test.sqlite").exists()
            )
            return result

    def _request(self) -> LiveSessionRequest:
        return LiveSessionRequest(
            prompt="prompt",
            artifact_scope=LiveSessionArtifactScope(
                domain="runner",
                scenario="codex",
            ),
            project_root=Path("/project"),
            plugin_root=Path("/plugin"),
            model="model",
            timeout=10,
            allowed_tools="tools",
            mcp_config="config",
        )


if __name__ == "__main__":
    unittest.main()

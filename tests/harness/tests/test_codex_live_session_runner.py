"""Verifies conversion of Codex CLI events into a typed live-session result."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from codex_live_session_runner import CodexLiveSessionRunner  # noqa: E402
from live_session_request import LiveSessionRequest  # noqa: E402
from live_session_result import LiveSessionResult  # noqa: E402


class TestCodexLiveSessionRunner(unittest.TestCase):

    def test_returns_child_thread_id_and_final_output(self) -> None:
        runner = CodexLiveSessionRunner()
        event_stream = '{"type":"thread.started","thread_id":"codex-child"}\n'

        result = self._run_with_output(runner, event_stream, "completed")

        self.assertEqual(result.session_id, "codex-child")
        self.assertEqual(result.final_output, "completed")

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
            result_path = Path(directory) / "last-message.txt"
            result_path.write_text(final_output, encoding="utf-8")
            with (
                patch(
                    "codex_live_session_runner.tempfile.mkdtemp",
                    return_value=directory,
                ),
                patch.object(runner, "_write_config"),
                patch.object(runner, "_link_auth"),
                patch.object(runner, "_install_plugin"),
                patch.object(runner, "_execute", return_value=event_stream),
            ):
                return runner.run(self._request())

    def _request(self) -> LiveSessionRequest:
        return LiveSessionRequest(
            prompt="prompt",
            project_root=Path("/project"),
            plugin_root=Path("/plugin"),
            model="model",
            timeout=10,
            allowed_tools="tools",
            mcp_config="config",
        )


if __name__ == "__main__":
    unittest.main()

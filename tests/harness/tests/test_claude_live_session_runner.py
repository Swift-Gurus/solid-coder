"""Verifies conversion of Claude CLI output into a typed live-session result."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_live_session_runner import ClaudeLiveSessionRunner  # noqa: E402
from live_session_request import LiveSessionRequest  # noqa: E402


class TestClaudeLiveSessionRunner(unittest.TestCase):

    def test_returns_child_session_id_and_final_output(self) -> None:
        completed = self._completed_process(
            json.dumps(
                [
                    {
                        "type": "system",
                        "subtype": "init",
                        "session_id": "claude-child",
                    },
                    {
                        "type": "result",
                        "session_id": "claude-child",
                        "result": "completed",
                    },
                ]
            )
        )

        with patch("claude_live_session_runner.subprocess.run", return_value=completed):
            result = ClaudeLiveSessionRunner().run(self._request())

        self.assertEqual(result.session_id, "claude-child")
        self.assertEqual(result.final_output, "completed")

    def test_rejects_output_without_child_session_id(self) -> None:
        completed = self._completed_process(json.dumps({"result": "completed"}))

        with patch("claude_live_session_runner.subprocess.run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "no session ID"):
                ClaudeLiveSessionRunner().run(self._request())

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

    def _completed_process(self, stdout: str) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout=stdout,
            stderr="",
        )


if __name__ == "__main__":
    unittest.main()

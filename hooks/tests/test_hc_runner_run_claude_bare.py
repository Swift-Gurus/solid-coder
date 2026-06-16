"""
solid-description: Validates model argument forwarding when executing bare Claude commands.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

import hook_utils  # noqa: E402
from capture_runner import CaptureRunner  # noqa: E402


class TestRunClaudeBareModel(unittest.TestCase):
    def _captured_cmd(self, **kwargs):
        capture = CaptureRunner([{"type": "result", "result": "ok"}])
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


if __name__ == "__main__":
    unittest.main()

"""
solid-description: Validates cwd parameter handling when executing bare Claude commands.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

import hook_utils  # noqa: E402
from capture_runner import CaptureRunner  # noqa: E402


class TestRunClaudeBareCwd(unittest.TestCase):
    def _captured_cwd(self, **kwargs):
        capture = CaptureRunner([{"type": "result", "result": "ok"}])
        hook_utils.run_claude_bare("hello", runner=capture, **kwargs)
        return capture.captured_cwd

    def test_cwd_forwarded_when_set(self):
        cwd = self._captured_cwd(cwd="/Users/alex/Developer/build-mobile")
        self.assertEqual(cwd, "/Users/alex/Developer/build-mobile")

    def test_cwd_omitted_when_empty(self):
        """Empty cwd must not be forwarded — subprocess.run(cwd="") raises FileNotFoundError."""
        cwd = self._captured_cwd(cwd="")
        self.assertIsNone(cwd)

    def test_cwd_omitted_when_unset(self):
        cwd = self._captured_cwd()
        self.assertIsNone(cwd)


if __name__ == "__main__":
    unittest.main()

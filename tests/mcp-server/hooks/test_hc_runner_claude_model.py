"""
solid-description: Verifies that initialization parameters are correctly forwarded during execution.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from hc_checker import ClaudeRunner  # noqa: E402


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


class TestClaudeRunnerCwd(unittest.TestCase):
    def _run_and_capture(self, cwd: str):
        captured = {}

        def fake_run_bare(prompt, **kwargs):
            captured.update(kwargs)
            return "ok"

        runner = ClaudeRunner(mcp_config="cfg", allowed_tools="tools", fn=fake_run_bare, cwd=cwd)
        runner.run("prompt", timeout=30)
        return captured

    def test_cwd_forwarded_to_run_bare(self):
        kw = self._run_and_capture("/Users/alex/Developer/build-mobile")
        self.assertEqual(kw.get("cwd"), "/Users/alex/Developer/build-mobile")

    def test_empty_cwd_forwarded_as_empty(self):
        kw = self._run_and_capture("")
        self.assertEqual(kw.get("cwd"), "")


if __name__ == "__main__":
    unittest.main()

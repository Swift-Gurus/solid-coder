"""
solid-description: Verifies that model specifications are correctly forwarded.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

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


if __name__ == "__main__":
    unittest.main()

"""Tests the gate workflow child-session bootstrap prompt."""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path


ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server",
    Path(__file__).resolve().parent,
)

from gate_flow_prompt_builder import GateFlowPromptBuilder  # noqa: E402


"""
solid-name: TestGateFlowPromptBuilder
solid-category: unit-test
solid-spec: [SPEC-036]
solid-description: Proves the child bootstrap carries source once and directs progression through the existing isolated run.
"""
class TestGateFlowPromptBuilder(unittest.TestCase):
    def test_builds_single_source_bootstrap_for_existing_run(self) -> None:
        source = "struct PendingView { let marker = 7391 }"

        prompt = GateFlowPromptBuilder().build(
            content=source,
            path="/project/Sources/PendingView.swift",
            parent_session_id="parent-session",
            run_id="gate-run",
            first_step="Measure SRP for PendingView.",
        )

        self.assertEqual(prompt.count(source), 1)
        self.assertTrue(prompt.startswith("# spawned-by: parent-session\n"))
        self.assertIn("/project/Sources/PendingView.swift", prompt)
        self.assertIn("gate-run", prompt)
        self.assertIn("Measure SRP for PendingView.", prompt)
        self.assertIn("flow_next", prompt)
        self.assertNotIn("flow_start", prompt)


if __name__ == "__main__":
    unittest.main()

"""
solid-name: test_run_state_reconstructor
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests reconstructing run state from parsed events, including attempt bookkeeping, reopened steps, and failed run status.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import StepOutputs
from harness.run_state_reconstructor_factory import make_run_state_reconstructor


class TestRunStateReconstructor(unittest.TestCase):

    def setUp(self):
        self.sut = make_run_state_reconstructor()

    def test_step_started_and_completed(self):
        state = self.sut.reconstruct([
            {"event": "step_started", "step_id": "load_principles"},
            {"event": "step_completed", "step_id": "load_principles", "outputs": {"principles": ["SRP"]}},
        ])
        self.assertIn("load_principles", state.completed)
        self.assertNotIn("load_principles", state.running)
        self.assertIsInstance(state.completed["load_principles"], StepOutputs)
        self.assertEqual(state.completed["load_principles"].get("principles"), ["SRP"])

    def test_turn_count_accumulates(self):
        state = self.sut.reconstruct([
            {"event": "turn_counted", "total": 1},
            {"event": "turn_counted", "total": 2},
        ])
        self.assertEqual(state.turn_count, 2)

    def test_run_completed_sets_done(self):
        state = self.sut.reconstruct([{"event": "run_completed"}])
        self.assertEqual(state.status, "done")

    def test_run_timed_out_sets_timed_out(self):
        state = self.sut.reconstruct([{"event": "run_timed_out"}])
        self.assertEqual(state.status, "timed_out")

    def test_step_attempt_failed_increments_attempts_without_touching_completed(self):
        state = self.sut.reconstruct([
            {"event": "step_completed", "step_id": "other", "outputs": {}},
            {"event": "step_attempt_failed", "step_id": "gate", "reason": "bad shape"},
            {"event": "step_attempt_failed", "step_id": "gate", "reason": "still bad"},
        ])
        self.assertEqual(state.attempts_used["gate"], 2)
        self.assertEqual(state.rejection_reasons["gate"], "still bad")
        self.assertIn("other", state.completed)
        self.assertNotIn("gate", state.completed)

    def test_step_rejected_increments_attempts_and_reopens_completed_step(self):
        state = self.sut.reconstruct([
            {"event": "step_completed", "step_id": "writer", "outputs": {"draft": "v1"}},
            {"event": "step_rejected", "step_id": "writer", "reason": "rejected by reviewer"},
        ])
        self.assertEqual(state.attempts_used["writer"], 1)
        self.assertEqual(state.rejection_reasons["writer"], "rejected by reviewer")
        self.assertNotIn("writer", state.completed)

    def test_run_failed_sets_failed_status(self):
        state = self.sut.reconstruct([
            {"event": "step_attempt_failed", "step_id": "gate", "reason": "boom"},
            {"event": "run_failed", "step_id": "gate"},
        ])
        self.assertEqual(state.status, "failed")


if __name__ == "__main__":
    unittest.main()

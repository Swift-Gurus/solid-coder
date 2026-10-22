"""Tests replay after a completed collection is rejected downstream."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.run_state_reconstructor_factory import make_run_state_reconstructor


"""
solid-name: TestRejectedForeachReplay
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies rejected collection outputs reopen their own instances without retaining stale child results or deleting unrelated work.
"""
class TestRejectedForeachReplay(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = make_run_state_reconstructor()
        self.events = [
            {"event": "step_completed", "step_id": step, "instance_id": instance,
             "iteration_index": index, "parent_completed": last,
             "workflow_instance_id": "nested", "local_step_id": step,
             "outputs": {"classification": value}}
            for step, instance, index, last, value in [
                ("classify", "opaque-a", 0, False, "old-a"),
                ("classify", "opaque-b", 1, True, "old-b"),
                ("unrelated", "opaque-c", 0, True, "keep"),
            ]
        ]
        self.events.append({"event": "step_rejected", "step_id": "classify", "reason": "Replace invalid identities"})

    def test_rejection_removes_its_instance_and_child_results_only(self) -> None:
        state = self.sut.reconstruct(self.events)
        self.assertNotIn("classify", state.completed)
        self.assertEqual(set(state.completed_instances), {"opaque-c"})
        self.assertEqual([entry.execution_step_id for entry in state.included_workflow_completions], ["unrelated"])
        self.assertIn("unrelated", state.completed)
        self.assertEqual(state.attempts_used["classify"], 1)
        self.assertEqual(state.rejection_reasons["classify"], "Replace invalid identities")

    def test_corrected_results_replace_rejected_child_results_on_replay(self) -> None:
        events = self.events + [
            {"event": "step_completed", "step_id": "classify", "instance_id": instance,
             "iteration_index": index, "parent_completed": index == 1,
             "workflow_instance_id": "nested", "local_step_id": "classify",
             "outputs": {"classification": value}}
            for index, instance, value in [(0, "opaque-a", "new-a"), (1, "opaque-b", "new-b")]
        ]
        state = self.sut.reconstruct(events)
        self.assertEqual(state.completed["classify"].get("classification"), ["new-a", "new-b"])
        self.assertEqual(
            [entry.outputs.get("classification") for entry in state.included_workflow_completions
             if entry.execution_step_id == "classify"],
            ["new-a", "new-b"],
        )

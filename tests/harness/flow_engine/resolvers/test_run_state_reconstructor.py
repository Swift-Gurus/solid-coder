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

from harness.comparison_condition import ComparisonCondition
from harness.comparison_condition_evidence import ComparisonConditionEvidence
from harness.condition_operator import ConditionOperator
from harness.models import StepOutputs
from harness.included_workflow_step_completion import IncludedWorkflowStepCompletion
from harness.run_state_reconstructor_factory import make_run_state_reconstructor
from harness.resolved_condition_value import ResolvedConditionValue
from harness.unavailable_condition_evidence import UnavailableConditionEvidence
from harness.workflow_expression import WorkflowExpression


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

    def test_restores_child_completion_with_explicit_nested_identity(self):
        state = self.sut.reconstruct([
            {
                "event": "step_completed",
                "step_id": "opaque-step-a7f4",
                "instance_id": "opaque-step-a7f4-1",
                "workflow_instance_id": "workflow-instance-7",
                "local_step_id": "inspect",
                "workflow_source_index": 0,
                "item": {"name": "Alpha"},
                "outputs": {"finding": "ok"},
            },
        ])

        self.assertEqual(
            state.included_workflow_completions,
            [
                IncludedWorkflowStepCompletion(
                    workflow_instance_id="workflow-instance-7",
                    local_step_id="inspect",
                    execution_step_id="opaque-step-a7f4",
                    instance_id="opaque-step-a7f4-1",
                    workflow_source_index=0,
                    item={"name": "Alpha"},
                    outputs=StepOutputs(values={"finding": "ok"}),
                )
            ],
        )

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

    def test_step_skipped_restores_terminal_condition_decision_without_attempts(self):
        state = self.sut.reconstruct([
            {"event": "step_started", "step_id": "inspect"},
            {
                "event": "step_skipped",
                "step_id": "inspect",
                "instance_id": "inspect-1",
                "condition": {
                    "ref": "{{params.enabled}}",
                    "equals": True,
                },
                "item": None,
                "parent_completed": True,
            },
        ])

        self.assertNotIn("inspect", state.running)
        self.assertEqual(
            state.skipped["inspect"].condition,
            ComparisonCondition(
                reference=WorkflowExpression(value="params.enabled"),
                operator=ConditionOperator.EQUALS,
                expected=True,
            ),
        )
        self.assertEqual(state.attempts_used, {})
        self.assertEqual(state.turn_count, 0)
        self.assertEqual(
            state.skipped["inspect"].evidence,
            UnavailableConditionEvidence(matched=False),
        )

    def test_step_skipped_restores_complete_audit_context_without_completing_parent(self):
        state = self.sut.reconstruct([
            {
                "event": "step_skipped",
                "step_id": "review",
                "instance_id": "review-2",
                "condition": {
                    "ref": "{{item.language}}",
                    "equals": "swift",
                },
                "evidence": {
                    "kind": "comparison",
                    "reference": "item.language",
                    "operator": "equals",
                    "expected": "swift",
                    "actual": {"present": True, "value": "kotlin"},
                    "matched": False,
                },
                "item": {"language": "kotlin"},
                "iteration_index": 1,
                "workflow_instance_id": "workflow-instance-7",
                "local_step_id": "inspect",
                "workflow_source_index": 0,
                "parent_completed": False,
            },
        ])

        skip = state.skipped_instances["review-2"]
        self.assertEqual(skip.step_id, "review")
        self.assertEqual(skip.instance_id, "review-2")
        self.assertEqual(skip.item, {"language": "kotlin"})
        self.assertEqual(skip.iteration_index, 1)
        self.assertEqual(skip.workflow_instance_id, "workflow-instance-7")
        self.assertEqual(skip.local_step_id, "inspect")
        self.assertEqual(skip.workflow_source_index, 0)
        self.assertEqual(
            skip.evidence,
            ComparisonConditionEvidence(
                reference="item.language",
                operator=ConditionOperator.EQUALS,
                expected="swift",
                actual=ResolvedConditionValue(
                    present=True,
                    value="kotlin",
                ),
                matched=False,
            ),
        )
        self.assertNotIn("review", state.skipped)

    def test_step_skipped_restores_explicit_child_scope(self):
        state = self.sut.reconstruct([
            {
                "event": "step_skipped",
                "step_id": "opaque-step-a7f4",
                "instance_id": "opaque-step-a7f4-1",
                "condition": {
                    "ref": "{{item.language}}",
                    "equals": "swift",
                },
                "workflow_instance_id": "workflow-instance-7",
                "local_step_id": "inspect",
                "workflow_source_index": 0,
                "parent_completed": True,
            },
        ])

        skip = state.skipped["opaque-step-a7f4"]
        self.assertEqual(skip.workflow_instance_id, "workflow-instance-7")
        self.assertEqual(skip.local_step_id, "inspect")
        self.assertEqual(skip.workflow_source_index, 0)

    def test_workflow_condition_evaluated_restores_decision_without_attempts(self):
        state = self.sut.reconstruct([
            {
                "event": "workflow_condition_evaluated",
                "condition": {
                    "ref": "{{params.enabled}}",
                    "equals": True,
                },
                "matched": False,
            },
        ])

        decision = state.workflow_condition_decision
        self.assertIsNotNone(decision)
        self.assertEqual(
            decision.condition,
            ComparisonCondition(
                reference=WorkflowExpression(value="params.enabled"),
                operator=ConditionOperator.EQUALS,
                expected=True,
            ),
        )
        self.assertFalse(decision.matched)
        self.assertEqual(
            decision.evidence,
            UnavailableConditionEvidence(matched=False),
        )
        self.assertEqual(state.attempts_used, {})
        self.assertEqual(state.turn_count, 0)

    def test_workflow_condition_evaluated_restores_audit_evidence(self):
        state = self.sut.reconstruct([
            {
                "event": "workflow_condition_evaluated",
                "condition": {
                    "ref": "{{params.enabled}}",
                    "equals": True,
                },
                "matched": True,
                "evidence": {
                    "kind": "comparison",
                    "reference": "params.enabled",
                    "operator": "equals",
                    "expected": True,
                    "actual": {"present": True, "value": True},
                    "matched": True,
                },
            },
        ])

        decision = state.workflow_condition_decision
        self.assertIsNotNone(decision)
        self.assertEqual(
            decision.evidence,
            ComparisonConditionEvidence(
                reference="params.enabled",
                operator=ConditionOperator.EQUALS,
                expected=True,
                actual=ResolvedConditionValue(present=True, value=True),
                matched=True,
            ),
        )
        self.assertTrue(decision.matched)


if __name__ == "__main__":
    unittest.main()

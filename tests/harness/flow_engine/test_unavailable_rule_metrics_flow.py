import sys
import tempfile
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.rule_review_result import RuleReviewResult
from harness.review_result import ReviewResult
from harness.step_result import StepResult
from harness.event_replayer import EventParser, EventReplayer
from harness.run_state_reconstructor_factory import make_run_state_reconstructor
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver


"""
solid-name: TestUnavailableRuleMetricsFlow
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies conditional metrics preserve unavailable outcomes without manufacturing compliant measurements during finalization and replay.
"""
class TestUnavailableRuleMetricsFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.driver = OperationWorkflowIntegrationDriver(self.root, [])
        self.driver.write_workflow("""
id: conditional-rule
name: Conditional measurement
rule: {}
steps:
  - id: observations
    prompt: Classify available evidence.
    outputs:
      - name: available
        type: data
        schema: {type: boolean}
      - name: entries
        type: data
        schema: {type: array, items: {type: string}}
  - id: score
    type: metric
    metric_id: CHECK-1
    unavailable_reason: Evidence is insufficient to evaluate this metric.
    depends_on: [observations]
    when:
      ref: "{{steps.observations.outputs.available}}"
      equals: true
    value: {type: integer, minimum: 0}
    scoring:
      source: "{{steps.observations.outputs.entries}}"
      severe: {operator: greater_than_or_equal, value: 2}
  - id: exception
    type: exception
    depends_on: [score]
    prompt: Classify the whole-rule exception.
""")

    def complete(self, available: bool) -> RuleReviewResult:
        started = self.driver.start()
        self.assertIsNone(started.error, started.error)
        ready = self.submit(started.steps[0], {"available": available, "entries": ["a", "b"]})
        self.assertIsNone(ready.error, ready.error)
        self.assertEqual([step.step_id for step in ready.steps], ["exception"])
        completed = self.submit(ready.steps[0], {
            "is_exception": False,
            "additional_info": {"reasoning": "Not exempt.", "evidence": "Behavioral declaration."},
        })
        self.assertEqual(completed.status, "done", completed.error)
        paths = list((self.root / "runs" / started.run_id / "results" / "review" / "conditional-rule").rglob("result.json"))
        self.assertEqual(len(paths), 1)
        self.run_id = started.run_id
        self.aggregate = ReviewResult.model_validate_json(
            (self.root / "runs" / started.run_id / "results" / "review" / "result.json").read_text()
        )
        return RuleReviewResult.model_validate_json(paths[0].read_text())

    def submit(self, step: StepResult, outputs: dict):
        if step.batch is None:
            return self.driver.advance({step.instance_id: outputs})
        return self.driver.advance({step.batch.label: {step.batch.workflow_alias: {step.step_id: outputs}}})

    def test_unavailable_metric_has_audit_evidence_and_no_score(self) -> None:
        result = self.complete(False)

        self.assertEqual(result.metrics, [])
        self.assertIsNone(result.severity)
        self.assertIsNone(self.aggregate.severity)
        self.assertEqual(len(result.unavailable_metrics), 1)
        outcome = result.unavailable_metrics[0]
        self.assertEqual(outcome.metric_id, "CHECK-1")
        self.assertEqual(outcome.status, "unavailable")
        self.assertTrue(outcome.additional_info.reasoning)
        self.assertIn("available", outcome.additional_info.evidence)
        self.assertNotIn("value", outcome.model_dump())
        self.assertNotIn("severity", outcome.model_dump())

    def test_available_metric_keeps_its_measured_severity(self) -> None:
        result = self.complete(True)

        self.assertEqual(result.metrics[0].value, 2)
        self.assertEqual(result.severity.value, "SEVERE")
        self.assertEqual(result.unavailable_metrics, [])

    def test_aggregate_submission_retains_unavailable_outcome(self) -> None:
        self.driver.write_workflow(self.driver.workflow_path.read_text().replace(
            "rule: {}",
            "rule: {}\nexecution: {mode: aggregate}\npresentation: {mode: combined}",
        ))

        result = self.complete(False)

        self.assertIsNone(result.severity)
        self.assertEqual(result.unavailable_metrics[0].metric_id, "CHECK-1")

    def test_replay_does_not_turn_unavailable_into_a_measurement(self) -> None:
        result = self.complete(False)
        events_path = self.root / "runs" / self.run_id / "events.jsonl"
        before = events_path.read_text()

        replayed = EventReplayer(EventParser(), make_run_state_reconstructor()).replay(str(events_path))

        self.assertEqual(replayed.status, "done")
        self.assertIn("score", replayed.skipped)
        self.assertNotIn("score", replayed.completed)
        self.assertEqual(result.unavailable_metrics[0].additional_info.evidence, replayed.skipped["score"].evidence.model_dump_json())
        self.assertEqual(events_path.read_text(), before)
        self.assertEqual(result.unavailable_metrics[0].status, "unavailable")

    def test_measured_severe_metric_survives_unavailable_sibling(self) -> None:
        self.driver.write_workflow(self.driver.workflow_path.read_text().replace(
            "  - id: exception",
            """  - id: measured
    type: metric
    metric_id: CHECK-2
    depends_on: [observations]
    value: {type: integer, minimum: 0}
    scoring:
      source: "{{steps.observations.outputs.entries}}"
      severe: {operator: greater_than_or_equal, value: 2}
  - id: exception""",
        ).replace("depends_on: [score]", "depends_on: [score, measured]"))

        result = self.complete(False)

        self.assertEqual([metric.metric_id for metric in result.metrics], ["CHECK-2"])
        self.assertEqual(result.metrics[0].value, 2)
        self.assertEqual(result.severity.value, "SEVERE")
        self.assertEqual(self.aggregate.severity.value, "SEVERE")
        self.assertEqual([metric.metric_id for metric in result.unavailable_metrics], ["CHECK-1"])

    def test_missing_classification_remains_pending_not_unavailable(self) -> None:
        started = self.driver.start()

        pending = self.driver.advance({})

        self.assertEqual(pending.status, "ready")
        self.assertEqual(pending.steps[0].instance_id, started.steps[0].instance_id)
        self.assertFalse((self.root / "runs" / started.run_id / "results" / "review").exists())

    def test_ordinary_conditional_skip_is_not_unavailable(self) -> None:
        self.driver.write_workflow(self.driver.workflow_path.read_text().replace(
            "    unavailable_reason: Evidence is insufficient to evaluate this metric.\n", "",
        ).replace("  - id: exception", """  - id: measured
    type: metric
    metric_id: CHECK-2
    depends_on: [observations]
    value: {type: integer, minimum: 0}
    scoring:
      source: "{{steps.observations.outputs.entries}}"
      severe: {operator: greater_than_or_equal, value: 2}
  - id: exception""").replace("depends_on: [score]", "depends_on: [score, measured]"))

        result = self.complete(False)

        self.assertEqual([metric.metric_id for metric in result.metrics], ["CHECK-2"])
        self.assertEqual(result.unavailable_metrics, [])

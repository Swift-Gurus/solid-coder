"""
solid-name: TestFrontmatterAggregateFlow
solid-category: integration-test
solid-spec: [SPEC-069]
solid-description: Verifies aggregate metadata judgments preserve partial results, recovery, replay, scoring and Stop enforcement across source operations.
"""

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "mcp-server"))
sys.path.insert(0, str(_ROOT / "mcp-server/hooks"))

from flow_transition_gate_factory import FlowTransitionGateFactory
from flow_transition_handler import FlowStopEvaluator
from harness.aggregate_batch_step_presentation import AggregateBatchStepPresentation
from harness.project_context import ProjectDirectory
from harness.review_result import ReviewResult
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from source.frontmatter.frontmatter_preparation import FrontmatterPreparation
from source.source_operation_registrations_factory import SourceOperationRegistrationsFactory


class TestFrontmatterAggregateFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.driver = OperationWorkflowIntegrationDriver(self.root,
            SourceOperationRegistrationsFactory(ProjectDirectory(path=self.root)).make(), _ROOT)
        self.driver.write_workflow('''
id: aggregate-frontmatter
name: Aggregate Frontmatter
execution: {mode: aggregate}
presentation: {mode: combined}
steps:
  - include: {workflow: frontmatter}
    as: metadata
    with:
      review_unit: "{{params.review_unit}}"
''')
        code = "\n".join(f"// solid-name: {name}\n// solid-category: service\n// solid-description: Provides deliveries.\nstruct {name} {{}}" for name in ["Alpha", "Beta"])
        self.started = self.driver.start({"review_unit": {"target": {"name": "Unwritten", "code": code, "source_identity": str(self.root / "Unwritten.swift")}}})
        self.assertIsNone(self.started.error, self.started.error)
        self.assertEqual(len(self.started.steps), 2)
        self.run = self.root / "runs" / self.started.run_id

    def test_partial_replay_and_stop_preserve_exact_once_source_operations(self) -> None:
        first, second = self.started.steps
        pending = self._submit(first, self._response(first))
        self.assertEqual([entry.instance_id for entry in pending.steps], [second.instance_id])
        resumed = self.driver.advance()
        gate = FlowStopEvaluator(FlowTransitionGateFactory(base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: self.root)).build())
        self.assertFalse(gate.evaluate_stop({}).allow)
        done = self._submit(resumed.steps[0], self._response(resumed.steps[0]))
        self.assertEqual(done.status, "done", done.error)
        self.assertTrue(gate.evaluate_stop({}).allow)
        result = ReviewResult.model_validate_json((self.run / "results/review/result.json").read_text())
        self.assertEqual([metric.value for metric in result.rule_results[0].metrics], [0, 0, 0, 0, 0])
        for step in ["analyze_source", "prepare_frontmatter", "bind_descriptions"]:
            self.assertEqual(sum(event.get("event") == "step_completed" and event.get("local_step_id") == step for event in self._events()), 1)

    def test_unrelated_identity_reopens_judgments_then_complete_correction_scores(self) -> None:
        pending = self.started
        for step in self.started.steps:
            output = self._response(step)
            output["classification"]["declaration_id"] = "unrelated"
            pending = self._submit(step, output)
        self.assertEqual(pending.status, "ready", pending.error)
        self.assertTrue(any("complete replacement" in (step.rejection_reason or "") for step in pending.steps))
        while pending.steps:
            step = pending.steps[0]
            pending = self._submit(step, self._response(step))
        self.assertEqual(pending.status, "done", pending.error)

    def _events(self):
        return [json.loads(line) for line in (self.run / "events.jsonl").read_text().splitlines()]

    def _response(self, step):
        event = next(event for event in self._events() if event.get("event") == "step_completed" and event.get("local_step_id") == "prepare_frontmatter")
        prepared = FrontmatterPreparation.model_validate(event["outputs"])
        target = next(entry for entry in prepared.descriptions if entry.label == step.batch.label)
        return {"classification": {"declaration_id": target.declaration_id, "classification": "CAPABILITY",
            "additional_info": {"reasoning": "Describes the capability.", "evidence": target.description}}}

    def _submit(self, step, output):
        if isinstance(step.batch, AggregateBatchStepPresentation):
            return self.driver.advance({step.batch.label: {step.batch.workflow_alias: {step.batch.authored_step.step_id: output}}})
        return self.driver.advance({step.batch.label: output})

"""Checks bundled Code Smells across aggregate submissions and replay."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

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
from source.analysis.declarations.source_declaration_selection_result import (
    SourceDeclarationSelectionResult,
)
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)

"""
solid-name: TestCodeSmellsAggregateFlow
solid-category: integration-test
solid-spec: [SPEC-066]
solid-description: Verifies real bundled source-backed scoring survives aggregate partial submissions, identity rejection, replay and Stop enforcement without rerunning preparation.
"""


class TestCodeSmellsAggregateFlow(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.driver = OperationWorkflowIntegrationDriver(
            self.root,
            SourceOperationRegistrationsFactory(
                ProjectDirectory(path=self.root)
            ).make(),
            _ROOT,
        )
        self.driver.write_workflow("""
id: aggregate-code-smells
name: Aggregate Code Smells
max_turns: 10
execution: {mode: aggregate}
presentation: {mode: combined}
steps:
  - id: targets
    prompt: Identify the prepared review files.
    outputs:
      - name: files
        type: data
        schema: {type: array, items: {type: object}}
  - include: {workflow: code-smells}
    as: checks
    depends_on: [targets]
    for_each:
      source: "{{steps.targets.outputs.files}}"
      mode: batch
      label: "{{item.target.name}}"
    with:
      review_unit: "{{item}}"
""")
        self.code = (
            _ROOT / "tests/principles/code-smells/fixtures/fixture-1.swift"
        ).read_text()
        initial = self.driver.start()
        self.started = self.submit(
            initial.steps[0],
            {
                "files": [
                    {
                        "target": {
                            "name": name,
                            "code": self.code,
                            "source_identity": str(self.root / (name + ".swift")),
                        }
                    }
                    for name in ["Alpha", "Beta"]
                ]
            },
        )
        self.assertIsNone(self.started.error, self.started.error)
        self.assertEqual(len(self.started.steps), 2)
        self.run = self.root / "runs" / initial.run_id

    def events(self):
        return [
            json.loads(line)
            for line in (self.run / "events.jsonl").read_text().splitlines()
        ]

    def response(self):
        selected = next(
            event
            for event in self.events()
            if event.get("event") == "step_completed"
            and event.get("local_step_id") == "select_declarations"
        )
        declarations = SourceDeclarationSelectionResult.model_validate(
            selected["outputs"]
        ).declarations
        return {
            "file_context": {
                "is_build_dsl": False,
                "additional_info": {
                    "reasoning": "Application source.",
                    "evidence": "ReportComposer",
                },
            },
            "classifications": [
                {
                    "kind": "independent",
                    "declaration_id": entry.identity,
                    "has_business_logic": entry.unit.name == "compose",
                    "additional_info": {
                        "reasoning": "Independent declaration.",
                        "evidence": entry.unit.name,
                    },
                }
                for entry in declarations
            ],
        }

    def submit(self, step, output):
        if not isinstance(step.batch, AggregateBatchStepPresentation):
            return self.driver.advance({step.batch.label: output})
        return self.driver.advance(
            {
                step.batch.label: {
                    step.batch.workflow_alias: {
                        step.batch.authored_step.step_id: output,
                    }
                }
            }
        )

    def assert_results(self):
        result = ReviewResult.model_validate_json(
            (self.run / "results/review/result.json").read_text()
        )
        self.assertEqual(len(result.rule_results), 2)
        for rule in result.rule_results:
            self.assertEqual([metric.value for metric in rule.metrics], [1, 2, 1])
            self.assertFalse(rule.exception.is_exception)
        completed = [
            event for event in self.events() if event["event"] == "step_completed"
        ]
        for step in ["analyze_source", "select_declarations", "bind_classifications"]:
            self.assertEqual(
                sum(event.get("local_step_id") == step for event in completed), 2
            )

    def test_partial_submission_and_replay_preserve_scoring_and_stop_blocks_pending_work(
        self,
    ):
        first, second = self.started.steps
        self.assertNotIn(self.code, first.prompt)
        pending = self.submit(first, self.response())
        self.assertEqual(
            [step.instance_id for step in pending.steps], [second.instance_id]
        )
        resumed = self.driver.advance()
        self.assertEqual(
            [step.instance_id for step in resumed.steps], [second.instance_id]
        )
        gate = FlowStopEvaluator(
            FlowTransitionGateFactory(
                base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: self.root),
            ).build()
        )
        self.assertFalse(gate.evaluate_stop({}).allow)
        done = self.submit(resumed.steps[0], self.response())
        self.assertEqual(done.status, "done", done.error)
        self.assertTrue(gate.evaluate_stop({}).allow)
        self.assert_results()

    def test_missing_declaration_reopens_only_affected_assignment(self):
        first, second = self.started.steps
        accepted = self.submit(first, self.response())
        invalid = self.response()
        invalid["classifications"].pop()
        rejected = self.submit(accepted.steps[0], invalid)
        self.assertEqual(
            [step.instance_id for step in rejected.steps], [second.instance_id]
        )
        self.assertIn("complete replacement", rejected.steps[0].rejection_reason)
        done = self.submit(rejected.steps[0], self.response())
        self.assertEqual(done.status, "done", done.error)
        self.assert_results()

    def test_invalid_contract_relationship_reopens_only_affected_assignment(self):
        first, second = self.started.steps
        accepted = self.submit(first, self.response())
        invalid = self.response()
        source = next(
            entry
            for entry in invalid["classifications"]
            if entry["additional_info"]["evidence"] == "ReportComposer"
        )
        target = next(
            entry
            for entry in invalid["classifications"]
            if entry["additional_info"]["evidence"] == "ReportEnvelope"
        )
        source.pop("has_business_logic")
        source["kind"] = "cohesive_contract"
        source["related_declaration_id"] = target["declaration_id"]

        rejected = self.submit(accepted.steps[0], invalid)

        self.assertEqual(
            [step.instance_id for step in rejected.steps], [second.instance_id]
        )
        self.assertIn(
            "both declarations must be protocols", rejected.steps[0].rejection_reason
        )
        self.assertIn("complete replacement", rejected.steps[0].rejection_reason)
        resumed = self.driver.advance()
        self.assertEqual(
            [step.instance_id for step in resumed.steps], [second.instance_id]
        )
        done = self.submit(resumed.steps[0], self.response())
        self.assertEqual(done.status, "done", done.error)
        self.assert_results()

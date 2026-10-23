import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.aggregate_batch_step_presentation import AggregateBatchStepPresentation
from harness.flow_validation_error import FlowValidationError
from harness.review_result import ReviewResult
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver

"""
solid-name: TestFixedRuleException
solid-category: integration-test
solid-spec: [SPEC-066]
solid-description: Verifies authored fixed rule exceptions remain validated and audited without a model classification step, including included workflow replay.
"""


class TestFixedRuleException(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.driver = OperationWorkflowIntegrationDriver(self.root, [])
        self.workflow = textwrap.dedent("""
            id: fixed-exception
            name: Fixed exception
            max_turns: 5
            rule:
              exception:
                is_exception: false
                additional_info:
                  reasoning: Only metric-specific exceptions apply.
                  evidence: This workflow declares no whole-rule exemption.
            steps:
              - id: measure
                type: metric
                metric_id: TEST-1
                prompt: Measure the target.
                value: {type: integer, minimum: 0}
                scoring:
                  severe: {operator: greater_than_or_equal, value: 1}
        """)

    def test_fixed_exception_is_audited_without_a_model_step(self) -> None:
        self.driver.write_workflow(self.workflow)
        started = self.driver.start()
        self.assertEqual([step.step_id for step in started.steps], ["measure"])

        completed = self.driver.advance(
            {
                started.steps[0].instance_id: {
                    "value": 2,
                    "additional_info": {
                        "reasoning": "Two observations.",
                        "evidence": "Source lines 1-2.",
                    },
                }
            }
        )

        self.assertEqual(completed.status, "done", completed.error)
        run = self.root / "runs" / started.run_id
        result = ReviewResult.model_validate_json(
            (run / "results/review/result.json").read_text()
        )
        self.assertFalse(result.rule_results[0].exception.is_exception)
        self.assertEqual(result.rule_results[0].severity, "SEVERE")
        events = [
            json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()
        ]
        self.assertEqual(
            sum(event["event"] == "exception_classified" for event in events), 1
        )

    def test_fixed_and_model_exception_are_mutually_exclusive(self) -> None:
        self.driver.write_workflow(
            self.workflow
            + textwrap.indent(
                textwrap.dedent("""
            - id: classify_exception
              type: exception
              prompt: Classify.
        """),
                "  ",
            )
        )

        with self.assertRaisesRegex(FlowValidationError, "exception"):
            self.driver.start()

    def test_fixed_exception_requires_reasoning_and_evidence(self) -> None:
        self.driver.write_workflow(
            self.workflow.replace(
                "      evidence: This workflow declares no whole-rule exemption.\n",
                "",
            )
        )

        with self.assertRaisesRegex(FlowValidationError, "evidence"):
            self.driver.start()

    def test_included_fixed_exception_survives_snapshot_and_replay(self) -> None:
        child = self.root / "workflows" / "child" / "workflow.yaml"
        child.parent.mkdir(parents=True)
        child.write_text(self.workflow)
        self.driver.write_workflow(
            textwrap.dedent("""
            id: parent
            name: Parent
            max_turns: 5
            execution: {mode: aggregate}
            presentation: {mode: combined}
            steps:
              - include: {workflow: fixed-exception}
                as: review
        """)
        )
        started = self.driver.start()
        child.unlink()
        resumed = self.driver.advance()
        self.assertEqual(resumed.steps[0].instance_id, started.steps[0].instance_id)

        batch = resumed.steps[0].batch
        self.assertIsInstance(batch, AggregateBatchStepPresentation)
        self.assertEqual(batch, started.steps[0].batch)
        completed = self.driver.advance(
            {
                batch.label: {
                    batch.workflow_alias: {
                        batch.authored_step.step_id: {
                            "value": 0,
                            "additional_info": {
                                "reasoning": "No observations.",
                                "evidence": "The target is empty.",
                            },
                        }
                    }
                }
            }
        )

        self.assertEqual(completed.status, "done", completed.error)
        result = ReviewResult.model_validate_json(
            (
                self.root / "runs" / started.run_id / "results/review/result.json"
            ).read_text(),
        )
        self.assertEqual(
            result.rule_results[0].exception.additional_info.reasoning,
            "Only metric-specific exceptions apply.",
        )

    def test_ineligible_fixed_rule_does_not_publish_unavailable_findings(self) -> None:
        child = self.root / "workflows" / "child" / "workflow.yaml"
        child.parent.mkdir(parents=True)
        child.write_text(
            self.workflow.replace(
                "    metric_id: TEST-1",
                "    metric_id: TEST-1\n    unavailable_reason: Missing evidence.",
            )
        )
        self.driver.write_workflow(
            textwrap.dedent("""
            id: excluded
            name: Excluded
            steps:
              - include: {workflow: fixed-exception}
                as: review
                when: {ref: "{{params.enabled}}", equals: true}
        """)
        )
        started = self.driver.start({"enabled": False})
        self.assertEqual(started.status, "done", started.error)
        self.assertFalse(
            (
                self.root / "runs" / started.run_id / "results/review/result.json"
            ).exists()
        )

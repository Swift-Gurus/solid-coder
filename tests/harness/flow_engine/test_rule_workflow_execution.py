"""
solid-name: TestRuleWorkflowExecution
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies metric and exception steps execute through the agent path with generated output validation.
"""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.review_result import ReviewResult
from harness.rule_review_result import RuleReviewResult
from harness.runs_base_dir_resolver import RunsBaseDirResolver


class TestRuleWorkflowExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.project_root = Path(temporary_directory.name)
        self.workflow_path = self.project_root / "workflow.yaml"
        self.workflow_path.write_text(
            textwrap.dedent(
                """
                id: executable-rule
                name: Executable Rule
                max_turns: 5
                rule: {}
                steps:
                  - id: smell_count
                    type: metric
                    metric_id: TEST-1
                    prompt: Count the smell.
                    value: {type: integer, minimum: 0}
                    scoring:
                      severe: {operator: greater_than, value: 1}
                  - id: classify_exception
                    type: exception
                    prompt: Classify the exception.
                """
            )
        )
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

    def test_executes_metric_and_exception_steps_through_agent_submission(self) -> None:
        started = self.sut.flow_start(str(self.workflow_path))

        self.assertEqual(
            {step.step_id for step in started.steps},
            {"smell_count", "classify_exception"},
        )
        outputs = {
            step.instance_id: self._output_for(step.step_id)
            for step in started.steps
        }

        completed = self.sut.flow_next(outputs)

        self.assertEqual(completed.status, "done")
        run_directory = self.project_root / "runs" / started.run_id
        review_result = self._rule_result(run_directory, started.run_id)
        aggregate_result = self._aggregate_result(run_directory)
        self.assertEqual(review_result.workflow_id, "executable-rule")
        self.assertEqual(review_result.rule_instance_id, started.run_id)
        self.assertEqual(review_result.severity, "SEVERE")
        self.assertEqual(review_result.scoring_authority, "mcp")
        self.assertFalse(review_result.exception.is_exception)
        self.assertEqual(review_result.metrics[0].metric_id, "TEST-1")
        self.assertEqual(review_result.metrics[0].severity, "SEVERE")
        self.assertEqual(aggregate_result.rule_results, [review_result])

        event_types = [
            json.loads(line)["event"]
            for line in (run_directory / "events.jsonl").read_text().splitlines()
        ]
        self.assertIn("metric_scored", event_types)
        self.assertIn("exception_classified", event_types)
        self.assertIn("rule_result_published", event_types)

    def test_rejects_metric_output_without_required_audit_information(self) -> None:
        started = self.sut.flow_start(str(self.workflow_path))
        outputs = {
            step.instance_id: (
                {"value": 2}
                if step.step_id == "smell_count"
                else self._output_for(step.step_id)
            )
            for step in started.steps
        }

        rejected = self.sut.flow_next(outputs)

        self.assertEqual(rejected.status, "ready")
        metric_step = next(
            step for step in rejected.steps if step.step_id == "smell_count"
        )
        self.assertIn("additional_info", metric_step.rejection_reason)

    def test_publishes_compliant_result_with_preserved_exception_audit(self) -> None:
        started = self.sut.flow_start(str(self.workflow_path))
        outputs = {
            step.instance_id: (
                {
                    "is_exception": True,
                    "additional_info": {
                        "reasoning": "This unit is a pure data structure.",
                        "evidence": "lines 1-6",
                    },
                }
                if step.step_id == "classify_exception"
                else self._output_for(step.step_id)
            )
            for step in started.steps
        }

        completed = self.sut.flow_next(outputs)

        self.assertEqual(completed.status, "done")
        run_directory = self.project_root / "runs" / started.run_id
        review_result = self._rule_result(run_directory, started.run_id)
        self.assertEqual(review_result.severity, "COMPLIANT")
        self.assertEqual(review_result.metrics[0].severity, "COMPLIANT")
        self.assertTrue(review_result.exception.is_exception)
        self.assertEqual(
            review_result.exception.additional_info.evidence,
            "lines 1-6",
        )

    @staticmethod
    def _rule_result(
        run_directory: Path,
        rule_instance_id: str,
    ) -> RuleReviewResult:
        result_path = (
            run_directory
            / "results"
            / "review"
            / "executable-rule"
            / rule_instance_id
            / "result.json"
        )
        return RuleReviewResult.model_validate_json(result_path.read_text())

    @staticmethod
    def _aggregate_result(run_directory: Path) -> ReviewResult:
        result_path = run_directory / "results" / "review" / "result.json"
        return ReviewResult.model_validate_json(result_path.read_text())

    def _output_for(self, step_id: str) -> dict:
        additional_info = {
            "reasoning": "The inspected source supports this observation.",
            "evidence": "line 12",
        }
        if step_id == "smell_count":
            return {"value": 2, "additional_info": additional_info}
        return {"is_exception": False, "additional_info": additional_info}


if __name__ == "__main__":
    unittest.main()

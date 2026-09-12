"""Proves aggregate rule observations use existing deterministic finalization."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import (  # noqa: E402
    FlowRunOrchestratorFactory,
)
from harness.review_result import ReviewResult  # noqa: E402
from harness.rule_review_result import RuleReviewResult  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402


"""
solid-name: TestAggregateRuleWorkflowExecution
solid-category: integration-test
solid-spec: [SPEC-044]
solid-description: Verifies one aggregate rule step is validated, scored, persisted, and audited through the existing rule finalizer.
"""
class TestAggregateRuleWorkflowExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.workflow_path = self.project_root / "workflow.yaml"
        self.workflow_path.write_text(
            textwrap.dedent(
                """
                id: aggregate-rule
                name: Aggregate Rule
                max_turns: 3
                rule: {}
                steps:
                  - id: assess
                    prompt: Assess every metric and the exception.
                    assessment:
                      metrics:
                        - metric_id: TEST-1
                          observation_id: count
                          value: {type: integer, minimum: 0}
                          scoring:
                            severe: {operator: greater_than, value: 1}
                        - metric_id: TEST-2
                          observation_id: blocked
                          value: {type: boolean}
                          scoring:
                            minor: {operator: equals, value: true}
                      exception_observation_id: exception
                """
            ),
            encoding="utf-8",
        )
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

    def test_scores_and_persists_every_aggregate_observation(self) -> None:
        started = self.sut.flow_start(str(self.workflow_path))

        self.assertEqual(len(started.steps), 1)
        completed = self.sut.flow_next({
            started.steps[0].instance_id: self._outputs(is_exception=False)
        })

        self.assertEqual(completed.status, "done", completed.error)
        run_directory = self.project_root / "runs" / started.run_id
        result = self._rule_result(run_directory, started.run_id)
        aggregate = ReviewResult.model_validate_json(
            (run_directory / "results" / "review" / "result.json").read_text()
        )
        self.assertEqual(result.scoring_authority, "mcp")
        self.assertEqual(result.severity, "SEVERE")
        count, blocked = result.metrics
        self.assertEqual(count.metric_id, "TEST-1")
        self.assertEqual(count.observation_id, "count")
        self.assertEqual(count.value, 2)
        self.assertEqual(count.severity, "SEVERE")
        self.assertEqual(blocked.metric_id, "TEST-2")
        self.assertEqual(blocked.observation_id, "blocked")
        self.assertIs(blocked.value, True)
        self.assertEqual(blocked.severity, "MINOR")
        self.assertEqual(aggregate.rule_results, [result])
        events = [
            json.loads(line)["event"]
            for line in (run_directory / "events.jsonl").read_text().splitlines()
        ]
        self.assertEqual(events.count("metric_scored"), 2)
        self.assertIn("exception_classified", events)
        self.assertIn("rule_result_published", events)

    def test_exception_makes_every_aggregate_metric_compliant(self) -> None:
        started = self.sut.flow_start(str(self.workflow_path))

        completed = self.sut.flow_next({
            started.steps[0].instance_id: self._outputs(is_exception=True)
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._rule_result(
            self.project_root / "runs" / started.run_id,
            started.run_id,
        )
        self.assertEqual(result.severity, "COMPLIANT")
        self.assertTrue(result.exception.is_exception)
        self.assertEqual(
            [metric.severity.value for metric in result.metrics],
            ["COMPLIANT", "COMPLIANT"],
        )

    def test_isolated_review_persists_result_in_canonical_run_directory(self) -> None:
        started = self.sut.flow_start(str(self.workflow_path), isolated=True)

        completed = self.sut.flow_next(
            {started.steps[0].instance_id: self._outputs(is_exception=False)},
            run_id=started.run_id,
        )

        run_directory = (
            self.project_root / "runs" / "subagents" / started.run_id
        )
        self.assertEqual(completed.status, "done", completed.error)
        self.assertTrue(
            (run_directory / "results" / "review" / "result.json").is_file()
        )
        self.assertFalse((run_directory / started.run_id).exists())

    def test_rejects_incomplete_aggregate_audit_information(self) -> None:
        started = self.sut.flow_start(str(self.workflow_path))
        outputs = self._outputs(is_exception=False)
        del outputs["count"]["additional_info"]

        rejected = self.sut.flow_next({
            started.steps[0].instance_id: outputs
        })

        self.assertEqual(rejected.status, "ready")
        self.assertIn("additional_info", rejected.steps[0].rejection_reason)

    @staticmethod
    def _outputs(is_exception: bool) -> dict:
        audit = {
            "reasoning": "The submitted source supports this observation.",
            "evidence": "line 12",
        }
        return {
            "count": {"value": 2, "additional_info": audit},
            "blocked": {"value": True, "additional_info": audit},
            "exception": {
                "is_exception": is_exception,
                "additional_info": audit,
            },
        }

    @staticmethod
    def _rule_result(
        run_directory: Path,
        rule_instance_id: str,
    ) -> RuleReviewResult:
        return RuleReviewResult.model_validate_json(
            (
                run_directory
                / "results"
                / "review"
                / "aggregate-rule"
                / rule_instance_id
                / "result.json"
            ).read_text()
        )


if __name__ == "__main__":
    unittest.main()

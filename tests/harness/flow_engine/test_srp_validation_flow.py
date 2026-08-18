"""
solid-name: test_srp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies packaged SRP observation, validation, scoring, and audit behavior through the flow engine.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.review_result import ReviewResult  # noqa: E402
from harness.rule_review_result import RuleReviewResult  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.static_session_id_reader import StaticSessionIdReader  # noqa: E402


_REVIEW_UNIT = """final class Example {
    func load() {}
    func save() {}
}"""
_METRIC_VALUES = {
    "verb_count": 6,
    "cohesion_groups": 2,
    "stakeholder_count": 2,
}


class TestSRPValidationFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=_PROJECT_ROOT,
            session_reader=StaticSessionIdReader("spec-039-test"),
        ).build()

    def test_starts_three_metrics_and_one_exception_without_scoring_step(self) -> None:
        started = self._start()

        self.assertEqual(
            {step.step_id for step in started.steps},
            {
                "verb_count",
                "cohesion_groups",
                "stakeholder_count",
                "classify_exception",
            },
        )
        self.assertNotIn("score_results", {step.step_id for step in started.steps})
        self.assertTrue(all(_REVIEW_UNIT in step.prompt for step in started.steps))

    def test_rejects_unaudited_measurement_before_scoring(self) -> None:
        started = self._start()
        metric = next(step for step in started.steps if step.step_id == "verb_count")

        rejected = self.sut.flow_next({metric.instance_id: {"value": 6}})

        self.assertEqual(rejected.status, "ready")
        rejected_metric = next(
            step for step in rejected.steps if step.step_id == "verb_count"
        )
        self.assertIn("additional_info", rejected_metric.rejection_reason)

    def test_mcp_scores_all_metrics_and_publishes_audited_result(self) -> None:
        started = self._start()

        completed = self.sut.flow_next(
            {
                step.instance_id: self._output_for(step.step_id)
                for step in started.steps
            }
        )

        self.assertEqual(completed.status, "done")
        review_directory = (
            self.project_root / "runs" / started.run_id / "results" / "review"
        )
        result_path = (
            review_directory
            / "solid-srp-review"
            / started.run_id
            / "result.json"
        )
        result = RuleReviewResult.model_validate_json(result_path.read_text())
        aggregate = ReviewResult.model_validate_json(
            (review_directory / "result.json").read_text()
        )
        self.assertEqual(result.workflow_id, "solid-srp-review")
        self.assertEqual(result.rule_instance_id, started.run_id)
        self.assertEqual(result.severity, "SEVERE")
        self.assertEqual(result.scoring_authority, "mcp")
        self.assertFalse(result.exception.is_exception)
        self.assertEqual(aggregate.rule_results, [result])
        self.assertEqual(
            [metric.metric_id for metric in result.metrics],
            ["SRP-1", "SRP-2", "SRP-3"],
        )
        self.assertEqual(
            [metric.value for metric in result.metrics],
            [6, 2, 2],
        )
        self.assertEqual(
            [metric.severity for metric in result.metrics],
            ["SEVERE", "SEVERE", "SEVERE"],
        )

    def _start(self):
        return self.sut.flow_start(
            "solid-srp-review",
            {"review_unit": _REVIEW_UNIT},
        )

    def _output_for(self, step_id: str) -> dict:
        additional_info = {
            "reasoning": f"Measured {step_id} from the supplied source.",
            "evidence": "Example lines 1-4",
        }
        if step_id == "classify_exception":
            return {
                "is_exception": False,
                "additional_info": additional_info,
            }
        return {
            "value": _METRIC_VALUES[step_id],
            "additional_info": additional_info,
        }


if __name__ == "__main__":
    unittest.main()

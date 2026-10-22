"""Defines the backend-neutral live LSP workflow expectations."""

from __future__ import annotations

from pathlib import Path

from harness.review_result import ReviewResult
from preserved_live_workflow_run import PreservedLiveWorkflowRun
from rule_validation_e2e_live_base import RuleValidationE2ELiveBase


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = _PROJECT_ROOT / "tests" / "principles" / "LSP" / "fixtures" / "fixture-1.swift"


"""
solid-name: LSPValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Supplies the LSP scenario and exact observations to the shared live executable-rule contract.
"""
class LSPValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "lsp"
    ARTIFACT_SCENARIO = "lsp"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS = [
        "type_checks",
        "contract_violations",
        "fatal_calls",
    ]
    EXPECTED_METRIC_IDS = [
        "LSP-1",
        "LSP-2",
        "LSP-3",
    ]
    EXPECTED_OBSERVATION_IDS = ["value", "value", "fatal_calls"]
    EXPECTED_VALUES = [0, 0, 1]
    EXPECTED_METRIC_SEVERITIES = [
        "COMPLIANT",
        "COMPLIANT",
        "SEVERE",
    ]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    ALLOW_AUXILIARY_STEPS = True
    EXPECTED_RULE_SOURCE_INDEX = 1
    EXPECTED_RULE_RESULT_COUNT = 2
    EXPECTED_UNAVAILABLE_METRIC_IDS = ["LSP-3", "LSP-4"]

    def assert_workflow(self, run: PreservedLiveWorkflowRun) -> None:
        super().assert_workflow(run)
        review = ReviewResult.model_validate_json(
            (run.run_directory / "results/review/result.json").read_text(),
        )
        result = next(
            result for result in review.rule_results
            if result.workflow_id == self.WORKFLOW_ID
            and result.provenance.source_index == self.EXPECTED_RULE_SOURCE_INDEX
        )
        self.assertEqual(
            [metric.metric_id for metric in result.unavailable_metrics],
            self.EXPECTED_UNAVAILABLE_METRIC_IDS,
        )
        for metric in result.unavailable_metrics:
            with self.subTest(metric=metric.metric_id):
                self.assertEqual(metric.observation_id, "value")
                self.assertTrue(metric.additional_info.reasoning)
                self.assertTrue(metric.additional_info.evidence)

"""Tests authoritative flow review-result loading."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from _path_bootstrap import ensure_on_path


ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server",
    Path(__file__).resolve().parent,
)

from findings.metric_additional_info import MetricAdditionalInfo  # noqa: E402
from findings.review_severity import ReviewSeverity  # noqa: E402
from flow_review_result_reader import FlowReviewResultReader  # noqa: E402
from harness.review_result import ReviewResult  # noqa: E402
from harness.rule_exception_decision import RuleExceptionDecision  # noqa: E402
from harness.rule_metric_decision import RuleMetricDecision  # noqa: E402
from harness.rule_review_provenance import RuleReviewProvenance  # noqa: E402
from harness.rule_review_result import RuleReviewResult  # noqa: E402


"""
solid-name: TestFlowReviewResultReader
solid-category: unit-test
solid-spec: [SPEC-036, SPEC-039]
solid-description: Proves gate decisions load only typed aggregate results from the selected flow run.
"""
class TestFlowReviewResultReader(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.runs_root = Path(temporary.name)
        self.base_directory = MagicMock()
        self.base_directory.resolve.return_value = self.runs_root
        self.sut = FlowReviewResultReader(self.base_directory)

    def test_reads_typed_aggregate_result(self) -> None:
        expected = self._result()
        result_path = (
            self.runs_root
            / "subagents"
            / "gate-run"
            / "results"
            / "review"
            / "result.json"
        )
        result_path.parent.mkdir(parents=True)
        result_path.write_text(expected.model_dump_json(), encoding="utf-8")

        self.assertEqual(self.sut.read("gate-run"), expected)

    def test_rejects_run_identity_with_path_components(self) -> None:
        with self.assertRaisesRegex(ValueError, "path component"):
            self.sut.read("../another-run")

    @staticmethod
    def _result() -> ReviewResult:
        additional_info = MetricAdditionalInfo(
            reasoning="One severe responsibility split.",
            evidence="Feature.swift:1-8",
        )
        return ReviewResult(
            workflow_id="solid-gate-on-write",
            severity=ReviewSeverity.SEVERE,
            rule_results=[
                RuleReviewResult(
                    workflow_id="srp",
                    rule_instance_id="rule-instance",
                    provenance=RuleReviewProvenance(
                        kind="included",
                        scope_identity="rule_reviews",
                        source_index=0,
                    ),
                    severity=ReviewSeverity.SEVERE,
                    exception=RuleExceptionDecision(
                        is_exception=False,
                        additional_info=additional_info,
                    ),
                    metrics=[
                        RuleMetricDecision(
                            metric_id="SRP-2",
                            value=2,
                            severity=ReviewSeverity.SEVERE,
                            additional_info=additional_info,
                        )
                    ],
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()

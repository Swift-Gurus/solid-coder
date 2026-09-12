"""Tests blocking-violation selection from scored review results."""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path


ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server",
    Path(__file__).resolve().parent,
)

from findings.metric_additional_info import MetricAdditionalInfo  # noqa: E402
from findings.review_severity import ReviewSeverity  # noqa: E402
from harness.review_result import ReviewResult  # noqa: E402
from harness.rule_exception_decision import RuleExceptionDecision  # noqa: E402
from harness.rule_metric_decision import RuleMetricDecision  # noqa: E402
from harness.rule_review_provenance import RuleReviewProvenance  # noqa: E402
from harness.rule_review_result import RuleReviewResult  # noqa: E402
from scored_review_violation_selector import (  # noqa: E402
    ScoredReviewViolationSelector,
)


"""
solid-name: TestScoredReviewViolationSelector
solid-category: unit-test
solid-spec: [SPEC-036, SPEC-039]
solid-description: Proves only server-scored severe metrics become blocking health violations.
"""
class TestScoredReviewViolationSelector(unittest.TestCase):
    def test_selects_severe_metrics_with_reasoning_and_evidence(self) -> None:
        severe_info = MetricAdditionalInfo(
            reasoning="The type has two independent cohesion groups.",
            evidence="Feature.swift:4-19",
        )
        minor_info = MetricAdditionalInfo(
            reasoning="The type exposes three actions.",
            evidence="Feature.swift:5-17",
        )
        result = ReviewResult(
            workflow_id="solid-gate-on-write",
            severity=ReviewSeverity.SEVERE,
            rule_results=[
                RuleReviewResult(
                    workflow_id="srp",
                    rule_instance_id="srp-instance",
                    provenance=RuleReviewProvenance(
                        kind="included",
                        scope_identity="rule_reviews",
                        source_index=0,
                    ),
                    severity=ReviewSeverity.SEVERE,
                    exception=RuleExceptionDecision(
                        is_exception=False,
                        additional_info=severe_info,
                    ),
                    metrics=[
                        RuleMetricDecision(
                            metric_id="SRP-1",
                            value=3,
                            severity=ReviewSeverity.MINOR,
                            additional_info=minor_info,
                        ),
                        RuleMetricDecision(
                            metric_id="SRP-2",
                            value=2,
                            severity=ReviewSeverity.SEVERE,
                            additional_info=severe_info,
                        ),
                    ],
                )
            ],
        )

        violations = ScoredReviewViolationSelector().select(result)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].principle, "srp")
        self.assertEqual(violations[0].metric_id, "SRP-2")
        self.assertEqual(violations[0].issue, severe_info.reasoning)
        self.assertEqual(violations[0].evidence, severe_info.evidence)


if __name__ == "__main__":
    unittest.main()

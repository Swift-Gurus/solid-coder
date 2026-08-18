"""
solid-name: TestMetricScoringEvaluator
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies deterministic scalar metric bands produce server-authoritative severity.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from findings.review_severity import ReviewSeverity
from harness.metric_band_matcher import MetricBandMatcher
from harness.metric_scoring_declaration import MetricScoringDeclaration
from harness.metric_scoring_evaluator import MetricScoringEvaluator


class TestMetricScoringEvaluator(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = MetricScoringEvaluator(MetricBandMatcher())

    def test_returns_highest_matching_severity(self) -> None:
        scoring = MetricScoringDeclaration(
            minor={"operator": "greater_than_or_equal", "value": 3},
            severe={"operator": "greater_than", "value": 5},
        )

        self.assertEqual(self.sut.evaluate(6, scoring), ReviewSeverity.SEVERE)

    def test_returns_minor_when_only_minor_band_matches(self) -> None:
        scoring = MetricScoringDeclaration(
            minor={"operator": "greater_than_or_equal", "value": 3},
            severe={"operator": "greater_than", "value": 5},
        )

        self.assertEqual(self.sut.evaluate(4, scoring), ReviewSeverity.MINOR)

    def test_returns_compliant_when_no_band_matches(self) -> None:
        scoring = MetricScoringDeclaration(
            severe={"operator": "greater_than", "value": 5},
        )

        self.assertEqual(self.sut.evaluate(2, scoring), ReviewSeverity.COMPLIANT)

    def test_evaluates_boolean_equality(self) -> None:
        scoring = MetricScoringDeclaration(
            severe={"operator": "equals", "value": True},
        )

        self.assertEqual(self.sut.evaluate(True, scoring), ReviewSeverity.SEVERE)
        self.assertEqual(self.sut.evaluate(False, scoring), ReviewSeverity.COMPLIANT)


if __name__ == "__main__":
    unittest.main()

"""Tests the generic engine-owned ratio operation."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.collection_ratio_input import CollectionRatioInput  # noqa: E402
from harness.collection_ratio_observation import (  # noqa: E402
    CollectionRatioObservation,
)
from harness.collection_ratio_operation import CollectionRatioOperation  # noqa: E402
from harness.ratio_value_calculator import RatioValueCalculator  # noqa: E402


"""
solid-name: TestCollectionRatioOperation
solid-category: unit-test
solid-spec: [SPEC-057]
solid-description: Verifies deterministic ratios and authored empty-collection values for nested workflow observations.
"""
class TestCollectionRatioOperation(unittest.TestCase):
    def test_counts_matching_included_observations(self) -> None:
        result = self._operation().execute(CollectionRatioInput(
            observations=[
                self._observation(matches=True),
                self._observation(matches=False),
                self._observation(matches=True, included=False),
            ],
            empty_value=1.0,
        ))

        self.assertEqual(result.value, 0.5)
        self.assertEqual(result.numerator_count, 1)
        self.assertEqual(result.denominator_count, 2)
        self.assertFalse(result.used_empty_value)

    def test_uses_authored_value_when_no_observation_is_included(self) -> None:
        result = self._operation().execute(CollectionRatioInput(
            observations=[],
            empty_value=1.0,
        ))

        self.assertEqual(result.value, 1.0)
        self.assertEqual(result.numerator_count, 0)
        self.assertEqual(result.denominator_count, 0)
        self.assertTrue(result.used_empty_value)

    @staticmethod
    def _observation(
        matches: bool,
        included: bool = True,
    ) -> CollectionRatioObservation:
        return CollectionRatioObservation(
            observation_id="requirement",
            matches=matches,
            included=included,
            reasoning="Classified from source evidence.",
            evidence="Candidate.swift:requirement",
        )

    @staticmethod
    def _operation() -> CollectionRatioOperation:
        return CollectionRatioOperation(RatioValueCalculator())


if __name__ == "__main__":
    unittest.main()

"""Exercises generic pair matching and transitive component semantics."""

import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.component_metrics.connected_index_groups import ConnectedIndexGroups
from harness.component_metrics.intersecting_pair_resolver import (
    IntersectingPairResolver,
)
from harness.component_metrics.pairwise_projection_evidence import (
    PairwiseProjectionEvidence,
)
from harness.strict_collection_value_matcher import StrictCollectionValueMatcher
from harness.strict_value_comparator import StrictValueComparator

"""
solid-name: TestPairwiseComponentGrouping
solid-category: unit-test
solid-spec: [SPEC-059]
solid-description: Verifies strict set intersection, transitive grouping, isolation, and permutation invariance independently of rule semantics.
"""


class TestPairwiseComponentGrouping(unittest.TestCase):
    def setUp(self) -> None:
        self.matcher = IntersectingPairResolver(
            StrictCollectionValueMatcher(StrictValueComparator())
        )
        self.grouper = ConnectedIndexGroups()

    def test_transitive_intersections_and_disjoint_sets_form_stable_groups(
        self,
    ) -> None:
        projections = [
            PairwiseProjectionEvidence(index=0, left=["a"], right=["a"]),
            PairwiseProjectionEvidence(index=1, left=["a", "b"], right=["a", "b"]),
            PairwiseProjectionEvidence(index=2, left=["b"], right=["b"]),
            PairwiseProjectionEvidence(index=3, left=["c"], right=["c"]),
        ]

        result = self._components(projections)

        self.assertEqual(result, [[0, 1, 2], [3]])

    def test_scalar_types_do_not_coerce_during_matching(self) -> None:
        projections = [
            PairwiseProjectionEvidence(index=2, left=[True], right=[True]),
            PairwiseProjectionEvidence(index=4, left=[1], right=[1]),
            PairwiseProjectionEvidence(index=6, left=[1.0], right=[1.0]),
            PairwiseProjectionEvidence(index=8, left=["1"], right=["1"]),
            PairwiseProjectionEvidence(index=10, left=[True], right=[True]),
        ]

        result = self._components(projections)

        self.assertEqual(result, [[2, 10], [4], [6], [8]])

    def test_empty_sets_remain_isolated(self) -> None:
        projections = [
            PairwiseProjectionEvidence(index=0, left=[], right=[]),
            PairwiseProjectionEvidence(index=1, left=[], right=[]),
        ]

        self.assertEqual(self._components(projections), [[0], [1]])

    def test_empty_collection_has_no_components(self) -> None:
        self.assertEqual(self._components([]), [])

    def test_different_projection_paths_are_undirected_and_order_invariant(
        self,
    ) -> None:
        projections = [
            PairwiseProjectionEvidence(index=0, left=["a", "a"], right=[]),
            PairwiseProjectionEvidence(index=1, left=["b"], right=["a"]),
            PairwiseProjectionEvidence(index=2, left=[], right=["b"]),
        ]

        for permutation in itertools.permutations(projections):
            with self.subTest(indexes=[item.index for item in permutation]):
                self.assertEqual(self._components(list(permutation)), [[0, 1, 2]])

    def _components(
        self, projections: list[PairwiseProjectionEvidence]
    ) -> list[list[int]]:
        return self.grouper.resolve(
            [item.index for item in projections],
            self.matcher.resolve(projections),
        )

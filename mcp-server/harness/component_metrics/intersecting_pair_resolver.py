"""Finds undirected matches between projected scalar sets."""

from typing import Protocol

from harness.collection_value_matching import CollectionValueMatching
from harness.component_metrics.indexed_relation_edge import IndexedRelationEdge
from harness.component_metrics.pairwise_projection_evidence import (
    PairwiseProjectionEvidence,
)

"""
solid-name: PairwiseEdgesResolving
solid-category: abstraction
solid-spec: [SPEC-059]
solid-description: Contract for resolving matching source-index pairs from projected collection sets.
"""


class PairwiseEdgesResolving(Protocol):
    def resolve(
        self, projections: list[PairwiseProjectionEvidence]
    ) -> list[IndexedRelationEdge]: ...


"""
solid-name: IntersectingPairResolver
solid-category: service
solid-spec: [SPEC-059]
solid-description: Finds undirected set intersections using strict membership while preserving stable source-index evidence.
"""


class IntersectingPairResolver(PairwiseEdgesResolving):
    def __init__(self, matcher: CollectionValueMatching) -> None:
        self._matcher = matcher

    def resolve(
        self, projections: list[PairwiseProjectionEvidence]
    ) -> list[IndexedRelationEdge]:
        edges: list[IndexedRelationEdge] = []
        for position, left in enumerate(projections):
            for right in projections[position + 1 :]:
                if any(
                    self._matcher.contains(right.right, value) for value in left.left
                ) or any(
                    self._matcher.contains(left.right, value) for value in right.left
                ):
                    edges.append(
                        IndexedRelationEdge(
                            left_index=min(left.index, right.index),
                            right_index=max(left.index, right.index),
                        )
                    )
        return sorted(edges, key=lambda edge: (edge.left_index, edge.right_index))

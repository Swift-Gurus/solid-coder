"""Derives component counts from filtered collection observations."""

from harness.collection_metric_projection_resolving import (
    CollectionMetricProjectionResolving,
)
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducing import CollectionMetricReducing
from harness.collection_metric_reduction_result import CollectionMetricReductionResult
from harness.component_metrics.component_metric_evidence import ComponentMetricEvidence
from harness.component_metrics.connected_index_groups import IndexComponentsResolving
from harness.component_metrics.intersecting_pair_resolver import PairwiseEdgesResolving
from harness.component_metrics.pairwise_projection_evidence import (
    PairwiseProjectionEvidence,
)
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry

"""
solid-name: ComponentCountMetricReducer
solid-category: service
solid-spec: [SPEC-059]
solid-description: Derives auditable component counts through typed projection, pair matching, and connected grouping capabilities.
"""


class ComponentCountMetricReducer(CollectionMetricReducing):
    def __init__(
        self,
        projection_resolver: CollectionMetricProjectionResolving[
            PairwiseProjectionEvidence
        ],
        edge_resolver: PairwiseEdgesResolving,
        component_resolver: IndexComponentsResolving,
    ) -> None:
        self._projection_resolver = projection_resolver
        self._edge_resolver = edge_resolver
        self._component_resolver = component_resolver

    def reduce(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> CollectionMetricReductionResult:
        projections = self._projection_resolver.resolve(declaration, entries)
        edges = self._edge_resolver.resolve(projections)
        components = self._component_resolver.resolve(
            [entry.source_index for entry in entries],
            edges,
        )
        return CollectionMetricReductionResult(
            value=len(components),
            component_evidence=ComponentMetricEvidence(
                projections=projections,
                edges=edges,
                components=components,
            ),
        )

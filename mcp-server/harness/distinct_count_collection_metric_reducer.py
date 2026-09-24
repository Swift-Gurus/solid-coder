"""Counts distinct projected collection metric values."""

from harness.collection_metric_projection_evidence import (
    CollectionMetricProjectionEvidence,
)
from harness.collection_metric_projection_resolving import (
    CollectionMetricProjectionResolving,
)
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducing import CollectionMetricReducing
from harness.collection_metric_reduction_result import (
    CollectionMetricReductionResult,
)
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry
from harness.strict_value_comparing import StrictValueComparing


"""
solid-name: DistinctCountCollectionMetricReducer
solid-category: strategy
solid-spec: [SPEC-054]
solid-description: Counts type-strict projected values while preserving first-occurrence evidence for audit.
"""
class DistinctCountCollectionMetricReducer(CollectionMetricReducing):
    def __init__(
        self,
        projection_resolver: CollectionMetricProjectionResolving,
        value_comparator: StrictValueComparing,
    ) -> None:
        self._projection_resolver = projection_resolver
        self._value_comparator = value_comparator

    def reduce(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> CollectionMetricReductionResult:
        evidence = self._projection_resolver.resolve(declaration, entries)
        distinct: list[CollectionMetricProjectionEvidence] = []
        for candidate in evidence:
            if any(
                self._value_comparator.equal(existing.value, candidate.value)
                for existing in distinct
            ):
                continue
            distinct.append(candidate)
        return CollectionMetricReductionResult(
            value=len(distinct),
            projection_evidence=evidence,
            distinct_indexes=[candidate.index for candidate in distinct],
        )

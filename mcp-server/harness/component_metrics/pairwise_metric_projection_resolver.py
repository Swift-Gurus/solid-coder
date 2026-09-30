"""Resolves typed left and right collection projections."""

from typing import Optional

from harness.collection_metric_projection_resolving import CollectionMetricProjectionResolving
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.component_metrics.pairwise_projection_evidence import PairwiseProjectionEvidence
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_scoring_band import MetricComparisonValue
from harness.nested_value_resolving import NestedValueResolving
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry
from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: PairwiseMetricProjectionResolver
solid-category: service
solid-spec: [SPEC-059]
solid-description: Resolves validated scalar sets for both sides of a collection relation while preserving source identity.
"""
class PairwiseMetricProjectionResolver(CollectionMetricProjectionResolving[PairwiseProjectionEvidence]):
    def __init__(
        self,
        path_resolver: NestedValueResolving,
        array_decoder: StructuredModelDecoding[list[Optional[MetricComparisonValue]]],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._path_resolver = path_resolver
        self._array_decoder = array_decoder
        self._error_factory = error_factory

    def resolve(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> list[PairwiseProjectionEvidence]:
        relation = declaration.relation
        if relation is None:
            raise self._error_factory.create("Component reducer requires a relation")
        return [
            PairwiseProjectionEvidence(
                index=entry.source_index,
                left=self._array_decoder.decode(
                    self._path_resolver.resolve(entry.value, relation.left_path, relation.left.value),
                    f"relation.left at source index {entry.source_index}",
                ),
                right=self._array_decoder.decode(
                    self._path_resolver.resolve(entry.value, relation.right_path, relation.right.value),
                    f"relation.right at source index {entry.source_index}",
                ),
            )
            for entry in entries
        ]

"""Reduces projected collection metric values to one configured extreme."""

from harness.collection_metric_projection_resolving import (
    CollectionMetricProjectionResolving,
)
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducing import CollectionMetricReducing
from harness.collection_metric_reduction_result import (
    CollectionMetricReductionResult,
)
from harness.collection_metric_value_selecting import (
    CollectionMetricValueSelecting,
)
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry


"""
solid-name: ExtremeCollectionMetricReducer
solid-category: service
solid-spec: [SPEC-054]
solid-description: Derives an auditable numeric extreme through an injected selection policy.
"""
class ExtremeCollectionMetricReducer(CollectionMetricReducing):
    def __init__(
        self,
        projection_resolver: CollectionMetricProjectionResolving,
        value_selector: CollectionMetricValueSelecting,
        reducer_name: str,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._projection_resolver = projection_resolver
        self._value_selector = value_selector
        self._reducer_name = reducer_name
        self._error_factory = error_factory

    def reduce(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> CollectionMetricReductionResult:
        evidence = self._projection_resolver.resolve(declaration, entries)
        if not evidence:
            if declaration.empty_value is None:
                raise self._error_factory.create(
                    f"{self._reducer_name} reducer cannot reduce an empty collection"
                )
            return CollectionMetricReductionResult(
                value=declaration.empty_value,
            )
        return CollectionMetricReductionResult(
            value=self._value_selector.select([item.value for item in evidence]),
            projection_evidence=evidence,
        )

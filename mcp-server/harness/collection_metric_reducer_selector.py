"""Applies the registered collection metric reducer."""

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducing import CollectionMetricReducing
from harness.collection_metric_reduction_result import CollectionMetricReductionResult
from harness.collection_metric_registration_selecting import CollectionMetricRegistrationSelecting
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry


"""
solid-name: CollectionMetricReducerSelector
solid-category: service
solid-spec: [SPEC-054, SPEC-059]
solid-description: Evaluates collection metrics through their registered reducer capabilities.
"""
class CollectionMetricReducerSelector(CollectionMetricReducing):
    def __init__(
        self,
        selector: CollectionMetricRegistrationSelecting[CollectionMetricReducing],
    ) -> None:
        self._selector = selector

    def reduce(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> CollectionMetricReductionResult:
        return self._selector.select(declaration.type).reduce(declaration, entries)

"""Selects and applies a registered collection metric reducer."""

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_registration import (
    CollectionMetricReducerRegistration,
)
from harness.collection_metric_reducing import CollectionMetricReducing
from harness.collection_metric_reduction_result import (
    CollectionMetricReductionResult,
)
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry


"""
solid-name: CollectionMetricReducerSelector
solid-category: service
solid-spec: [SPEC-054]
solid-description: Routes a validated reducer declaration to its registered deterministic evaluation capability.
"""
class CollectionMetricReducerSelector(CollectionMetricReducing):
    def __init__(
        self,
        registrations: list[CollectionMetricReducerRegistration],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._registrations = registrations
        self._error_factory = error_factory

    def reduce(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> CollectionMetricReductionResult:
        registration = next(
            (
                candidate
                for candidate in self._registrations
                if candidate.reducer_type == declaration.type
            ),
            None,
        )
        if registration is None:
            raise self._error_factory.create(
                f"No runtime reducer is registered for '{declaration.type.value}'"
            )
        return registration.reducer.reduce(declaration, entries)

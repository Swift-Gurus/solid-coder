"""Selects registered reducer capabilities for decoding or evaluation."""

from typing import Generic, TypeVar

from harness.collection_metric_reducer_registration import (
    CollectionMetricReducerRegistration,
)
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.collection_metric_registration_selecting import (
    CollectionMetricRegistrationSelecting,
)
from harness.flow_validation_error_creating import FlowValidationErrorCreating

CapabilityT = TypeVar("CapabilityT")


"""
solid-name: CollectionMetricRegistrationSelector
solid-category: service
solid-spec: [SPEC-059]
solid-description: Provides registered reducer capabilities with explicit diagnostics for missing registrations.
"""


class CollectionMetricRegistrationSelector(
    CollectionMetricRegistrationSelecting[CapabilityT], Generic[CapabilityT]
):
    def __init__(
        self,
        registrations: list[CollectionMetricReducerRegistration[CapabilityT]],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._registrations = registrations
        self._error_factory = error_factory

    def select(self, reducer_type: CollectionMetricReducerType) -> CapabilityT:
        registration = next(
            (
                entry
                for entry in self._registrations
                if entry.reducer_type == reducer_type
            ),
            None,
        )
        if registration is None:
            raise self._error_factory.create(
                f"No capability is registered for reducer '{reducer_type.value}'"
            )
        return registration.reducer

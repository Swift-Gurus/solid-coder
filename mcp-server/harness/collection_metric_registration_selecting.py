"""Defines lookup of registered reducer capabilities."""

from typing import Protocol, TypeVar

from harness.collection_metric_reducer_type import CollectionMetricReducerType

CapabilityT_co = TypeVar("CapabilityT_co", covariant=True)


"""
solid-name: CollectionMetricRegistrationSelecting
solid-category: abstraction
solid-spec: [SPEC-059]
solid-description: Contract for selecting registered reducer capabilities.
"""


class CollectionMetricRegistrationSelecting(Protocol[CapabilityT_co]):
    def select(self, reducer_type: CollectionMetricReducerType) -> CapabilityT_co: ...

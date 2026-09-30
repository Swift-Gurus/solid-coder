"""Defines projection of filtered collection metric observations."""

from typing import Protocol, TypeVar
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry

ProjectionT = TypeVar("ProjectionT")

"""
solid-name: CollectionMetricProjectionResolving
solid-category: abstraction
solid-spec: [SPEC-054]
solid-description: Contract for resolving typed auditable projections from filtered observations.
"""
class CollectionMetricProjectionResolving(Protocol[ProjectionT]):
    def resolve(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> list[ProjectionT]: ...

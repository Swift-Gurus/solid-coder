"""Defines projection of filtered collection metric observations."""

from typing import Protocol

from harness.collection_metric_projection_evidence import (
    CollectionMetricProjectionEvidence,
)
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry


"""
solid-name: CollectionMetricProjectionResolving
solid-category: abstraction
solid-spec: [SPEC-054]
solid-description: Contract for resolving auditable scalar projections from filtered observations.
"""
class CollectionMetricProjectionResolving(Protocol):
    def resolve(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> list[CollectionMetricProjectionEvidence]: ...

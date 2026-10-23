"""Defines deterministic collection metric reduction."""

from typing import Protocol

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reduction_result import (
    CollectionMetricReductionResult,
)
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry

"""
solid-name: CollectionMetricReducing
solid-category: abstraction
solid-spec: [SPEC-054]
solid-description: Contract for deriving an auditable metric value from filtered observations.
"""


class CollectionMetricReducing(Protocol):
    def reduce(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> CollectionMetricReductionResult: ...

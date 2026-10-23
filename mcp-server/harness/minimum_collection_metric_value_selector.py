"""Selects the minimum projected collection metric value."""

from harness.collection_metric_value_selecting import (
    CollectionMetricValueSelecting,
)

"""
solid-name: MinimumCollectionMetricValueSelector
solid-category: strategy
solid-spec: [SPEC-054]
solid-description: Selects the least value from validated numeric metric projections.
"""


class MinimumCollectionMetricValueSelector(CollectionMetricValueSelecting):
    def select(self, values: list[object]) -> int | float:
        return min(values)

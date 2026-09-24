"""Selects the maximum projected collection metric value."""

from typing import Union

from harness.collection_metric_value_selecting import (
    CollectionMetricValueSelecting,
)


"""
solid-name: MaximumCollectionMetricValueSelector
solid-category: strategy
solid-spec: [SPEC-054]
solid-description: Selects the greatest value from validated numeric metric projections.
"""
class MaximumCollectionMetricValueSelector(CollectionMetricValueSelecting):
    def select(self, values: list[object]) -> Union[int, float]:
        return max(values)

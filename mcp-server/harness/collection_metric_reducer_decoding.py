"""Defines collection metric reducer decoding."""

from __future__ import annotations

from typing import Protocol

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.metric_value_type import MetricValueType

"""
solid-name: CollectionMetricReducerDecoding
solid-category: abstraction
solid-spec: [SPEC-054]
solid-description: Contract for decoding a collection reducer from workflow input.
"""


class CollectionMetricReducerDecoding(Protocol):
    def decode(
        self,
        step_id: str,
        raw: object,
        metric_value_type: MetricValueType,
        collection_backed: bool,
    ) -> CollectionMetricReducer | None: ...

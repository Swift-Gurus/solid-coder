"""Enforces declared metric value compatibility after reducer decoding."""

from __future__ import annotations

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_decoding import CollectionMetricReducerDecoding
from harness.collection_metric_registration_selecting import CollectionMetricRegistrationSelecting
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_reducer_value_compatibility import MetricReducerValueCompatibility
from harness.metric_value_type import MetricValueType


"""
solid-name: MetricCompatibleReducerDecoder
solid-category: decorator
solid-spec: [SPEC-054, SPEC-059]
solid-description: Ensures decoded reducers produce values compatible with their declared metrics.
"""
class MetricCompatibleReducerDecoder(CollectionMetricReducerDecoding):
    def __init__(
        self,
        delegate: CollectionMetricReducerDecoding,
        selector: CollectionMetricRegistrationSelecting[MetricReducerValueCompatibility],
        integer_compatibility: MetricReducerValueCompatibility,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._delegate = delegate
        self._selector = selector
        self._integer_compatibility = integer_compatibility
        self._error_factory = error_factory

    def decode(
        self,
        step_id: str,
        raw: object,
        metric_value_type: MetricValueType,
        collection_backed: bool,
    ) -> CollectionMetricReducer | None:
        reducer = self._delegate.decode(step_id, raw, metric_value_type, collection_backed)
        if reducer is None and not collection_backed:
            return None
        compatibility = (
            self._integer_compatibility if reducer is None
            else self._selector.select(reducer.type)
        )
        if metric_value_type not in compatibility.allowed_types:
            label = "collection-backed" if reducer is None else f"{reducer.type.value} reducer"
            raise self._error_factory.create(
                f"Metric step '{step_id}' {label} metric value must be "
                f"{compatibility.expected_description}"
            )
        if (
            reducer is not None
            and reducer.empty_value is not None
            and metric_value_type in self._integer_compatibility.allowed_types
            and not isinstance(reducer.empty_value, int)
        ):
            raise self._error_factory.create(
                f"Metric step '{step_id}' reducer empty_value must match "
                f"metric value type {metric_value_type.value}"
            )
        return reducer

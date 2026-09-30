"""Decodes typed reducer declarations through registered capabilities."""

from __future__ import annotations

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_decoding import CollectionMetricReducerDecoding
from harness.collection_metric_reducer_declaration import CollectionMetricReducerDeclaration
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.collection_metric_registration_selecting import CollectionMetricRegistrationSelecting
from harness.metric_value_type import MetricValueType
from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: CollectionMetricReducerDecoder
solid-category: boundary
solid-spec: [SPEC-054, SPEC-059]
solid-description: Decodes authored collection metrics through their registered reducer capabilities.
"""
class CollectionMetricReducerDecoder(CollectionMetricReducerDecoding):
    def __init__(
        self,
        declaration_decoder: StructuredModelDecoding[CollectionMetricReducerDeclaration],
        selector: CollectionMetricRegistrationSelecting[StructuredModelDecoding[CollectionMetricReducer]],
        type_decoder: StructuredModelDecoding[CollectionMetricReducerType],
    ) -> None:
        self._declaration_decoder = declaration_decoder
        self._selector = selector
        self._type_decoder = type_decoder

    def decode(
        self,
        step_id: str,
        raw: object,
        metric_value_type: MetricValueType,
        collection_backed: bool,
    ) -> CollectionMetricReducer | None:
        if raw is None:
            return None
        description = f"Metric step '{step_id}' scoring.reducer"
        declaration = self._declaration_decoder.decode(raw, description)
        reducer_type = self._type_decoder.decode(declaration.type, description)
        return self._selector.select(reducer_type).decode(declaration, description)

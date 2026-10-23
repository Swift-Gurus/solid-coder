"""Decodes connected-component metric reducers."""

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.component_metric_reducer_declaration import (
    ComponentMetricReducerDeclaration,
)
from harness.pairwise_relation import PairwiseRelation
from harness.structured_model_decoding import StructuredModelDecoding

"""
solid-name: ComponentMetricReducerDecoder
solid-category: boundary
solid-spec: [SPEC-059]
solid-description: Translates component metric reducer input into a validated reducer model.
"""


class ComponentMetricReducerDecoder(StructuredModelDecoding[CollectionMetricReducer]):
    def __init__(
        self,
        decoder: StructuredModelDecoding[ComponentMetricReducerDeclaration],
        relation_decoder: StructuredModelDecoding[PairwiseRelation],
        reducer_type_decoder: StructuredModelDecoding[CollectionMetricReducerType],
    ) -> None:
        self._decoder = decoder
        self._relation_decoder = relation_decoder
        self._reducer_type_decoder = reducer_type_decoder

    def decode(self, value: object, description: str) -> CollectionMetricReducer:
        declaration = self._decoder.decode(value, description)
        return CollectionMetricReducer(
            type=self._reducer_type_decoder.decode(
                declaration.type, f"{description} type"
            ),
            relation=self._relation_decoder.decode(
                declaration.relation, f"{description} relation"
            ),
        )

"""Decodes numerator and denominator metric reducers."""

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.condition_parsing import ConditionParsing
from harness.ratio_metric_reducer_declaration import RatioMetricReducerDeclaration
from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: RatioMetricReducerDecoder
solid-category: boundary
solid-spec: [SPEC-054, SPEC-059]
solid-description: Decodes ratio metrics from authored numerator and denominator conditions.
"""
class RatioMetricReducerDecoder(StructuredModelDecoding[CollectionMetricReducer]):
    def __init__(
        self,
        decoder: StructuredModelDecoding[RatioMetricReducerDeclaration],
        condition_parser: ConditionParsing,
    ) -> None:
        self._decoder = decoder
        self._condition_parser = condition_parser

    def decode(self, value: object, description: str) -> CollectionMetricReducer:
        declaration = self._decoder.decode(value, description)
        return CollectionMetricReducer(
            type=CollectionMetricReducerType.RATIO,
            empty_value=declaration.empty_value,
            numerator_condition=self._condition_parser.parse(declaration.numerator_when),
            denominator_condition=self._condition_parser.parse(declaration.denominator_when),
        )

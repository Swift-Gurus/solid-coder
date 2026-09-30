"""Decodes scalar projection metric reducers."""

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.projected_metric_reducer_declaration import ProjectedMetricReducerDeclaration
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_expression_parsing import WorkflowExpressionParsing


"""
solid-name: ProjectedMetricReducerDecoder
solid-category: boundary
solid-spec: [SPEC-054, SPEC-059]
solid-description: Decodes scalar projection reducers for deterministic collection metrics.
"""
class ProjectedMetricReducerDecoder(StructuredModelDecoding[CollectionMetricReducer]):
    def __init__(
        self,
        decoder: StructuredModelDecoding[ProjectedMetricReducerDeclaration],
        expression_parser: WorkflowExpressionParsing,
        item_path_decoder: StructuredModelDecoding[list[str]],
    ) -> None:
        self._decoder = decoder
        self._expression_parser = expression_parser
        self._item_path_decoder = item_path_decoder

    def decode(self, value: object, description: str) -> CollectionMetricReducer:
        declaration = self._decoder.decode(value, description)
        self._item_path_decoder.decode(declaration.value, f"{description} value")
        return CollectionMetricReducer(
            type=CollectionMetricReducerType(declaration.type),
            value=self._expression_parser.parse(declaration.value),
            empty_value=declaration.empty_value,
        )

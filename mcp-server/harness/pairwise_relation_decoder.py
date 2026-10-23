"""Decodes pairwise references once at the workflow boundary."""

from harness.pairwise_relation import PairwiseRelation
from harness.pairwise_relation_declaration import PairwiseRelationDeclaration
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_expression_parsing import WorkflowExpressionParsing

"""
solid-name: PairwiseRelationDecoder
solid-category: boundary
solid-spec: [SPEC-059]
solid-description: Decodes authored pairwise workflow relations for deterministic collection grouping.
"""


class PairwiseRelationDecoder(StructuredModelDecoding[PairwiseRelation]):
    def __init__(
        self,
        decoder: StructuredModelDecoding[PairwiseRelationDeclaration],
        expression_parser: WorkflowExpressionParsing,
        left_path_decoder: StructuredModelDecoding[list[str]],
        right_path_decoder: StructuredModelDecoding[list[str]],
    ) -> None:
        self._decoder = decoder
        self._expression_parser = expression_parser
        self._left_path_decoder = left_path_decoder
        self._right_path_decoder = right_path_decoder

    def decode(self, value: object, description: str) -> PairwiseRelation:
        declaration = self._decoder.decode(value, description)
        return PairwiseRelation(
            operator=declaration.operator,
            left=self._expression_parser.parse(declaration.left),
            right=self._expression_parser.parse(declaration.right),
            left_path=self._left_path_decoder.decode(
                declaration.left, f"{description}.left"
            ),
            right_path=self._right_path_decoder.decode(
                declaration.right, f"{description}.right"
            ),
        )

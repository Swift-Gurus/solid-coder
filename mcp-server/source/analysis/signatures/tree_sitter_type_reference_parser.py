"""Converts a syntax type reference to typed tokens and source evidence."""

from source.analysis.signatures.source_type_reference import SourceTypeReference
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_line_range import SourceLineRange
from tree_sitter import Node

"""
solid-name: TreeSitterTypeReferenceParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Converts an authored type reference into ordered tokens and source evidence without resolving its declaration.
"""


class TreeSitterTypeReferenceParser(SourceSyntaxParsing[Node, SourceTypeReference]):
    def __init__(
        self,
        tokens: SourceSyntaxParsing[Node, list[str]],
        spans: SourceSyntaxParsing[Node, SourceLineRange],
    ) -> None:
        self._tokens = tokens
        self._spans = spans

    def parse(self, source: Node) -> SourceTypeReference:
        return SourceTypeReference(
            tokens=self._tokens.parse(source), span=self._spans.parse(source)
        )

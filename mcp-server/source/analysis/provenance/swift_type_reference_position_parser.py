"""Finds a unique explicit Swift type token for semantic lookup."""

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from tree_sitter import Node

"""
solid-name: SwiftTypeReferencePositionParser
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Identifies an unambiguous explicit type position in Swift syntax.
"""


class SwiftTypeReferencePositionParser(SourceSyntaxParsing[Node, int | None]):
    def __init__(self, nodes: SourceSyntaxParsing[Node, list[Node]]) -> None:
        self._nodes = nodes

    def parse(self, source: Node) -> int | None:
        if source.type == "type_identifier":
            return source.start_byte
        references = [
            node for node in self._nodes.parse(source) if node.type == "user_type"
        ]
        if len(references) != 1:
            return None
        components = [
            node for node in references[0].named_children if not node.is_extra
        ]
        if not components or any(node.type != "type_identifier" for node in components):
            return None
        return components[-1].start_byte

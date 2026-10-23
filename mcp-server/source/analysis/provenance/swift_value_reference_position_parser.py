"""Selects a value identifier or the actual invoked symbol from Swift syntax."""

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from tree_sitter import Node

"""
solid-name: SwiftValueReferencePositionParser
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Locates exact identifier and callee positions without substituting receiver or argument symbols for the inspected expression.
"""


class SwiftValueReferencePositionParser(SourceSyntaxParsing[Node, int | None]):
    def parse(self, source: Node) -> int | None:
        if source.type == "simple_identifier":
            return source.start_byte
        if source.type != "call_expression" or not source.named_children:
            return None
        callee = source.named_children[0]
        if callee.type == "navigation_expression":
            suffix = callee.child_by_field_name("suffix")
            callee = (
                suffix.child_by_field_name("suffix") if suffix is not None else None
            )
        return (
            callee.start_byte
            if callee is not None and callee.type == "simple_identifier"
            else None
        )

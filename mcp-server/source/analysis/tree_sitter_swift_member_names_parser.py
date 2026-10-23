"""Extracts declared member names from Swift syntax."""

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftMemberNamesParser
solid-category: boundary-adapter
solid-spec: [SPEC-057, SPEC-062]
solid-description: Identifies Swift member names including lifecycle declarations, subscripts, and property bindings.
"""


class TreeSitterSwiftMemberNamesParser(SourceSyntaxParsing[Node, list[Node]]):
    def __init__(self, bindings: SourceSyntaxParsing[Node, list[Node]]) -> None:
        self._bindings = bindings

    def parse(self, source: Node) -> list[Node]:
        if source.type in {
            "init_declaration",
            "deinit_declaration",
            "subscript_declaration",
        }:
            return [
                child
                for child in source.children
                if child.type in {"init", "deinit", "subscript"}
            ]
        if source.type not in {"property_declaration", "protocol_property_declaration"}:
            name = source.child_by_field_name("name")
            return (
                [name] if name is not None and not name.is_missing and name.text else []
            )
        names: list[Node] = []
        for node in source.children_by_field_name("name"):
            names.extend(
                self._bindings.parse(node) if node.type == "pattern" else [node]
            )
        return [name for name in names if not name.is_missing and name.text]

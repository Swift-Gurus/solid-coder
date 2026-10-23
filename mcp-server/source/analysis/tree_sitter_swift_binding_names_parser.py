"""Reads the names introduced by Swift binding patterns."""

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftBindingNamesParser
solid-category: boundary-adapter
solid-spec: [SPEC-057, SPEC-062]
solid-description: Identifies all names introduced by simple and nested Swift property bindings.
"""


class TreeSitterSwiftBindingNamesParser(SourceSyntaxParsing[Node, list[Node]]):
    def parse(self, source: Node) -> list[Node]:
        names: list[Node] = []
        for child in source.named_children:
            if child.type == "simple_identifier":
                names.append(child)
            elif child.type == "pattern":
                names.extend(self.parse(child))
        return names

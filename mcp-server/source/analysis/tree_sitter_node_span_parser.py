"""Converts parser positions to inclusive source lines."""

from tree_sitter import Node

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_line_range import SourceLineRange


"""
solid-name: TreeSitterNodeSpanParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Resolves inclusive source line evidence for parsed declarations and syntax facts.
"""
class TreeSitterNodeSpanParser(SourceSyntaxParsing[Node, SourceLineRange]):
    def parse(self, source: Node) -> SourceLineRange:
        return SourceLineRange(
            start=source.start_point.row + 1,
            end=max(
                source.start_point.row + 1,
                source.end_point.row + (source.end_point.column > 0),
            ),
        )

"""Extracts ordered syntax tokens without whitespace or comments."""

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from tree_sitter import Node

"""
solid-name: TreeSitterSyntaxTokensParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Preserves ordered, case-sensitive syntax tokens and punctuation while omitting formatting and comment trivia.
"""


class TreeSitterSyntaxTokensParser(SourceSyntaxParsing[Node, list[str]]):
    def parse(self, source: Node) -> list[str]:
        if source.is_extra or source.is_missing:
            return []
        if source.child_count == 0:
            return [source.text.decode("utf-8")] if source.text else []
        return [token for child in source.children for token in self.parse(child)]

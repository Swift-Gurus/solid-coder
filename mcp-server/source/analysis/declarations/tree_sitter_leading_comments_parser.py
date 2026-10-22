"""Preserves comments attached to declarations independently of their contents."""

from tree_sitter import Node

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_evidence import SourceEvidence
from source.source_line_range import SourceLineRange


"""
solid-name: TreeSitterLeadingCommentsParser
solid-category: boundary-adapter
solid-spec: [SPEC-069]
solid-description: Associates leading source comments with their following declaration and retains source evidence.
"""
class TreeSitterLeadingCommentsParser(SourceSyntaxParsing[Node, list[SourceEvidence]]):
    def __init__(
        self,
        spans: SourceSyntaxParsing[Node, SourceLineRange],
        comment_node_types: frozenset[str],
    ) -> None:
        self._spans = spans
        self._comment_node_types = comment_node_types

    def parse(self, source: Node) -> list[SourceEvidence]:
        parent = source.parent
        if parent is None:
            return []
        text = parent.text
        if text is None:
            raise ValueError("Source text is required to associate declaration comments")
        comments: list[SourceEvidence] = []
        cursor = source
        preceding = cursor.prev_named_sibling
        while preceding is not None and preceding.type in self._comment_node_types:
            gap = text[
                preceding.end_byte - parent.start_byte:
                cursor.start_byte - parent.start_byte
            ]
            if gap.strip():
                break
            comment = preceding.text
            if comment is None:
                raise ValueError("Source text is required to preserve declaration comments")
            comments.append(SourceEvidence(
                fact=comment.decode("utf-8"),
                span=self._spans.parse(preceding),
            ))
            cursor = preceding
            preceding = cursor.prev_named_sibling
        return list(reversed(comments))

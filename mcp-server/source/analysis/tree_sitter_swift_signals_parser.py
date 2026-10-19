"""Extracts auditable code signals without comment or literal text."""

from tree_sitter import Node

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_evidence import SourceEvidence
from source.source_line_range import SourceLineRange


"""
solid-name: TreeSitterSwiftSignalsParser
solid-category: boundary-adapter
solid-spec: [SPEC-057, SPEC-063]
solid-description: Identifies Swift syntax signals and their source evidence while excluding comments and literal text.
"""
class TreeSitterSwiftSignalsParser(SourceSyntaxParsing[Node, list[SourceEvidence]]):
    def __init__(
        self,
        spans: SourceSyntaxParsing[Node, SourceLineRange],
        nodes: SourceSyntaxParsing[Node, list[Node]],
    ) -> None:
        self._spans = spans
        self._nodes = nodes

    def parse(self, source: Node) -> list[SourceEvidence]:
        signals: list[SourceEvidence] = []
        for node in self._nodes.parse(source):
            if node.child_count == 0 and node.text:
                text = node.text.decode("utf-8")
                if text.isidentifier():
                    signals.append(SourceEvidence(fact=text, span=self._spans.parse(node)))
        return signals

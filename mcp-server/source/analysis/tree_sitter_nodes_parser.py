"""Enumerates syntax nodes in source order with declared trivia exclusions."""

from tree_sitter import Node

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


"""
solid-name: TreeSitterNodesParser
solid-category: boundary-adapter
solid-spec: [SPEC-063]
solid-description: Enumerates a syntax tree in preorder while pruning configured node kinds and fields for language-selected consumers.
"""
class TreeSitterNodesParser(SourceSyntaxParsing[Node, list[Node]]):
    def __init__(
        self,
        excluded_node_types: frozenset[str],
        excluded_fields: frozenset[str],
    ) -> None:
        self._excluded_node_types = excluded_node_types
        self._excluded_fields = excluded_fields

    def parse(self, source: Node) -> list[Node]:
        nodes: list[Node] = []
        pending = [source]
        while pending:
            node = pending.pop()
            if node.type in self._excluded_node_types:
                continue
            nodes.append(node)
            pending.extend(reversed([
                child for index, child in enumerate(node.children)
                if node.field_name_for_child(index) not in self._excluded_fields
            ]))
        return nodes

"""Extracts restrictions from a Swift associated-type declaration."""

from source.analysis.signatures.source_associated_type_signature import (
    SourceAssociatedTypeSignature,
)
from source.analysis.signatures.swift_member_syntax import SwiftMemberSyntax
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftAssociatedTypeSignatureParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Preserves associated-type bounds, default types, and where clauses as syntax facts for later structural resolution.
"""


class TreeSitterSwiftAssociatedTypeSignatureParser(
    SourceSyntaxParsing[SwiftMemberSyntax, SourceAssociatedTypeSignature]
):
    def __init__(self, tokens: SourceSyntaxParsing[Node, list[str]]) -> None:
        self._tokens = tokens

    def parse(self, source: SwiftMemberSyntax) -> SourceAssociatedTypeSignature:
        return SourceAssociatedTypeSignature(
            bounds=self._clause(source.declaration, ":"),
            default_type=self._clause(source.declaration, "="),
            constraints=[
                token
                for node in source.declaration.named_children
                if node.type == "type_constraints"
                for token in self._tokens.parse(node)
            ],
        )

    def _clause(self, declaration: Node, delimiter: str) -> list[str]:
        tokens: list[str] = []
        selected = False
        for child in declaration.children:
            if child.type in {":", "=", "type_constraints"}:
                selected = child.type == delimiter
            elif selected:
                tokens.extend(self._tokens.parse(child))
        return tokens

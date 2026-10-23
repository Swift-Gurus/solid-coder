"""Extracts authored Swift declaration headers without resolving their symbols."""

from source.analysis.signatures.source_declaration_signature import (
    SourceDeclarationSignature,
)
from source.analysis.signatures.source_type_reference import SourceTypeReference
from source.analysis.signatures.source_unresolved_signature import (
    SourceUnresolvedSignature,
)
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_unit import SourceUnitSignature
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftDeclarationSignatureParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Extracts declaration names, inherited references, generic constraints, and modifiers while retaining unresolved syntax rather than asserting semantic relationships.
"""


class TreeSitterSwiftDeclarationSignatureParser(
    SourceSyntaxParsing[Node, SourceUnitSignature]
):
    def __init__(
        self,
        tokens: SourceSyntaxParsing[Node, list[str]],
        references: SourceSyntaxParsing[Node, SourceTypeReference],
    ) -> None:
        self._tokens = tokens
        self._references = references

    def parse(self, source: Node) -> SourceUnitSignature:
        if source.has_error:
            return SourceUnresolvedSignature(
                reason="Declaration syntax is incomplete or invalid"
            )
        if source.type not in {"class_declaration", "protocol_declaration"}:
            return SourceUnresolvedSignature(
                reason="This declaration has no supported nominal header"
            )
        name = source.child_by_field_name("name")
        if name is None or name.is_missing:
            return SourceUnresolvedSignature(reason="Declaration name is unavailable")
        return SourceDeclarationSignature(
            name=self._references.parse(name),
            inherited_types=[
                self._references.parse(node)
                for node in source.named_children
                if node.type == "inheritance_specifier"
            ],
            generic_parameters=[
                token
                for node in source.named_children
                if node.type == "type_parameters"
                for token in self._tokens.parse(node)
            ],
            constraints=[
                token
                for node in source.named_children
                if node.type == "type_constraints"
                for token in self._tokens.parse(node)
            ],
            modifiers=[
                token
                for node in source.named_children
                if node.type == "modifiers"
                for token in self._tokens.parse(node)
            ],
        )

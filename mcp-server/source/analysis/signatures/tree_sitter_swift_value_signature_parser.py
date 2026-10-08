"""Extracts one Swift property binding's declared signature."""

from tree_sitter import Node

from source.analysis.signatures.source_unresolved_signature import SourceUnresolvedSignature
from source.analysis.signatures.source_value_signature import SourceValueSignature
from source.analysis.signatures.swift_member_syntax import SwiftMemberSyntax
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


"""
solid-name: TreeSitterSwiftValueSignatureParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Extracts each property's explicit type, accessors, and modifiers while retaining unresolved inferred or destructured types.
"""
class TreeSitterSwiftValueSignatureParser(SourceSyntaxParsing[SwiftMemberSyntax, SourceValueSignature | SourceUnresolvedSignature]):
    def __init__(
        self,
        tokens: SourceSyntaxParsing[Node, list[str]],
        accessors: SourceSyntaxParsing[Node, list[str]],
    ) -> None:
        self._tokens = tokens
        self._accessors = accessors

    def parse(self, source: SwiftMemberSyntax) -> SourceValueSignature | SourceUnresolvedSignature:
        binding = next((
            node for node in source.declaration.children_by_field_name("name")
            if node.child_by_field_name("bound_identifier") == source.name
        ), None)
        if binding is None:
            return SourceUnresolvedSignature(reason="Destructured property type requires additional analysis")
        annotation = binding.next_named_sibling
        if annotation is None or annotation.type != "type_annotation":
            return SourceUnresolvedSignature(reason="Inferred property type requires semantic analysis")
        accessors = self._accessors.parse(source.declaration)
        if not accessors:
            return SourceUnresolvedSignature(reason="Property accessor syntax is unavailable or unsupported")
        return SourceValueSignature(
            value_type=[
                token for node in annotation.named_children
                for token in self._tokens.parse(node)
            ],
            accessors=accessors,
            modifiers=[
                token for node in source.declaration.named_children if node.type == "modifiers"
                for token in self._tokens.parse(node)
            ],
        )

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
    def __init__(self, tokens: SourceSyntaxParsing[Node, list[str]]) -> None:
        self._tokens = tokens

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
        accessors = self._accessors(source.declaration)
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

    def _accessors(self, declaration: Node) -> list[str]:
        body = next((
            node for node in declaration.named_children
            if node.type in {"protocol_property_requirements", "computed_property"}
        ), None)
        if body is None:
            bindings = [
                child for node in [declaration, *declaration.children_by_field_name("name")]
                for child in node.named_children if child.type == "value_binding_pattern"
            ]
            mutable = any("var" in self._tokens.parse(node) for node in bindings)
            return ["get", "set"] if mutable else ["get"]
        specifiers = [
            child for node in body.named_children for child in [node, *node.named_children]
            if child.type in {"getter_specifier", "setter_specifier"}
        ]
        if specifiers:
            return [token for node in specifiers for token in self._tokens.parse(node)]
        if any(node.type == "statements" for node in body.named_children):
            return ["get"]
        return []

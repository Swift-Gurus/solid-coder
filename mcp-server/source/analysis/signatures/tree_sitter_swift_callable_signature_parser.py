"""Extracts Swift method and lifecycle declaration signatures."""

from source.analysis.signatures.source_callable_signature import SourceCallableSignature
from source.analysis.signatures.source_parameter_signature import (
    SourceParameterSignature,
)
from source.analysis.signatures.swift_member_syntax import SwiftMemberSyntax
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftCallableSignatureParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Maps callable declaration syntax into parameter, result, modifier, and constraint facts without retaining implementation bodies.
"""


class TreeSitterSwiftCallableSignatureParser(
    SourceSyntaxParsing[SwiftMemberSyntax, SourceCallableSignature]
):
    def __init__(
        self,
        tokens: SourceSyntaxParsing[Node, list[str]],
        parameters: SourceSyntaxParsing[Node, list[SourceParameterSignature]],
    ) -> None:
        self._tokens = tokens
        self._parameters = parameters

    def parse(self, source: SwiftMemberSyntax) -> SourceCallableSignature:
        declaration = source.declaration
        return SourceCallableSignature(
            parameters=self._parameters.parse(declaration),
            return_type=[
                token
                for node in declaration.named_children
                if node.start_byte >= source.name.end_byte
                and (
                    node in declaration.children_by_field_name("name")
                    or node.type == "type_modifiers"
                )
                for token in self._tokens.parse(node)
            ],
            modifiers=[
                token
                for node in declaration.children
                if node.type
                in {
                    "modifiers",
                    "async",
                    "throws",
                    "throws_clause",
                    "rethrows",
                    "?",
                    "!",
                }
                for token in (["throws"] if node.type == "throws_clause" else [])
                + self._tokens.parse(node)
            ],
            generic_parameters=[
                token
                for node in declaration.named_children
                if node.type == "type_parameters"
                for token in self._tokens.parse(node)
            ],
            constraints=[
                token
                for node in declaration.named_children
                if node.type == "type_constraints"
                for token in self._tokens.parse(node)
            ],
        )

"""Extracts caller-visible parameter facts from Swift callable syntax."""

from source.analysis.signatures.source_parameter_signature import (
    SourceParameterSignature,
)
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftParametersParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Extracts ordered external argument labels and parameter types while preserving parameter modifiers and excluding implementation names and defaults.
"""


class TreeSitterSwiftParametersParser(
    SourceSyntaxParsing[Node, list[SourceParameterSignature]]
):
    def __init__(self, tokens: SourceSyntaxParsing[Node, list[str]]) -> None:
        self._tokens = tokens

    def parse(self, source: Node) -> list[SourceParameterSignature]:
        parameters: list[SourceParameterSignature] = []
        for parameter in source.named_children:
            if parameter.type != "parameter":
                continue
            external = parameter.child_by_field_name("external_name")
            name = external or parameter.child_by_field_name("name")
            separator = next(
                (child for child in parameter.children if child.type == ":"), None
            )
            if name is None or separator is None:
                raise ValueError("Parameter label or declared type is unavailable")
            type_tokens: list[str] = []
            for child in parameter.children:
                if child.type == "=":
                    break
                if child.start_byte >= separator.end_byte:
                    type_tokens.extend(self._tokens.parse(child))
            if not type_tokens:
                raise ValueError("Parameter declared type is unavailable")
            parameters.append(
                SourceParameterSignature(
                    external_label=(
                        "_"
                        if source.type == "subscript_declaration" and external is None
                        else name.text.decode("utf-8")
                    ),
                    type_tokens=type_tokens,
                )
            )
        return parameters

"""Extracts lexical ancestry from the already-parsed Swift syntax tree."""

from source.analysis.declarations.source_scope import SourceScope
from source.analysis.declarations.source_scope_kind import SourceScopeKind
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_line_range import SourceLineRange
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftScopeParser
solid-category: boundary-adapter
solid-spec: [SPEC-066]
solid-description: Decodes enclosing Swift type, callable, accessor, and closure scopes from syntax ancestry without parsing again or applying review policy.
"""


class TreeSitterSwiftScopeParser(SourceSyntaxParsing[Node, list[SourceScope]]):
    def __init__(self, spans: SourceSyntaxParsing[Node, SourceLineRange]) -> None:
        self._spans = spans

    def parse(self, source: Node) -> list[SourceScope]:
        scopes: list[SourceScope] = []
        ancestor = source.parent
        while ancestor is not None:
            match ancestor.type:
                case "class_declaration" | "protocol_declaration":
                    kind = SourceScopeKind.TYPE
                case (
                    "function_declaration"
                    | "protocol_function_declaration"
                    | "init_declaration"
                    | "deinit_declaration"
                    | "subscript_declaration"
                    | "computed_property"
                    | "willset_didset_block"
                ):
                    kind = SourceScopeKind.CALLABLE
                case "lambda_literal":
                    kind = SourceScopeKind.CLOSURE
                case _:
                    ancestor = ancestor.parent
                    continue
            name = ancestor.child_by_field_name("name")
            scopes.append(
                SourceScope(
                    identity=f"scope:{ancestor.start_byte}:{ancestor.end_byte}",
                    kind=kind,
                    name=name.text.decode("utf-8")
                    if name is not None and name.text
                    else ancestor.type,
                    span=self._spans.parse(ancestor),
                )
            )
            ancestor = ancestor.parent
        return list(reversed(scopes))

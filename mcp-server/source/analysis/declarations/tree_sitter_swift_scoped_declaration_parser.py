"""Enriches the shared Swift declaration parser with lexical scope facts."""

from source.analysis.declarations.source_scope import SourceScope
from source.analysis.declarations.source_scope_kind import SourceScopeKind
from source.analysis.declarations.source_scoped_declaration import (
    SourceScopedDeclaration,
)
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_evidence import SourceEvidence
from source.source_unit import SourceUnit
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftScopedDeclarationParser
solid-category: boundary-adapter
solid-spec: [SPEC-066, SPEC-069]
solid-description: Captures lexical scope, declaration metadata, modifiers, comments, and signals for each Swift declaration, including nested declarations.
"""


class TreeSitterSwiftScopedDeclarationParser(
    SourceSyntaxParsing[Node, SourceScopedDeclaration | None]
):
    def __init__(
        self,
        units: SourceSyntaxParsing[Node, SourceUnit | None],
        scopes: SourceSyntaxParsing[Node, list[SourceScope]],
        tokens: SourceSyntaxParsing[Node, list[str]],
        comments: SourceSyntaxParsing[Node, list[SourceEvidence]],
        signals: SourceSyntaxParsing[Node, list[SourceEvidence]],
        scope_kinds: SourceSyntaxParsing[list[SourceScope], SourceScopeKind],
    ) -> None:
        self._units = units
        self._scopes = scopes
        self._tokens = tokens
        self._comments = comments
        self._signals = signals
        self._scope_kinds = scope_kinds

    def parse(self, source: Node) -> SourceScopedDeclaration | None:
        unit = self._units.parse(source)
        if unit is None:
            return None
        scopes = self._scopes.parse(source)
        return SourceScopedDeclaration(
            identity=f"declaration:{source.start_byte}:{source.end_byte}",
            unit=unit,
            scopes=scopes,
            scope_kind=self._scope_kinds.parse(scopes),
            leading_comments=self._comments.parse(source),
            signals=self._signals.parse(source),
            modifiers=[
                token
                for child in source.children
                if child.type == "modifiers"
                or (source.type == "function_declaration" and child.type == "class")
                for token in self._tokens.parse(child)
            ],
        )

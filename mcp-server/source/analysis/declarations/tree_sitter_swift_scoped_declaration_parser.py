"""Enriches the shared Swift declaration parser with lexical scope facts."""

from tree_sitter import Node

from source.analysis.declarations.source_scope import SourceScope
from source.analysis.declarations.source_scope_kind import SourceScopeKind
from source.analysis.declarations.source_scoped_declaration import SourceScopedDeclaration
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_unit import SourceUnit


"""
solid-name: TreeSitterSwiftScopedDeclarationParser
solid-category: boundary-adapter
solid-spec: [SPEC-066]
solid-description: Reuses declaration, scope, and modifier parsing to record source-unique nested declarations without changing top-level review units.
"""
class TreeSitterSwiftScopedDeclarationParser(SourceSyntaxParsing[Node, SourceScopedDeclaration | None]):
    def __init__(
        self,
        units: SourceSyntaxParsing[Node, SourceUnit | None],
        scopes: SourceSyntaxParsing[Node, list[SourceScope]],
        tokens: SourceSyntaxParsing[Node, list[str]],
    ) -> None:
        self._units = units
        self._scopes = scopes
        self._tokens = tokens

    def parse(self, source: Node) -> SourceScopedDeclaration | None:
        unit = self._units.parse(source)
        if unit is None:
            return None
        scopes = self._scopes.parse(source)
        scope_kind = next(
            (kind for kind in (SourceScopeKind.CALLABLE, SourceScopeKind.CLOSURE, SourceScopeKind.TYPE)
             if any(scope.kind is kind for scope in scopes)),
            SourceScopeKind.FILE,
        )
        return SourceScopedDeclaration(
            identity=f"declaration:{source.start_byte}:{source.end_byte}",
            unit=unit,
            scopes=scopes,
            scope_kind=scope_kind,
            modifiers=[
                token for child in source.children
                if child.type == "modifiers" or (
                    source.type == "function_declaration" and child.type == "class"
                )
                for token in self._tokens.parse(child)
            ],
        )

"""Selects a declaration's governing lexical scope."""

from source.analysis.declarations.source_scope import SourceScope
from source.analysis.declarations.source_scope_kind import SourceScopeKind
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing

"""
solid-name: SourceScopeKindResolver
solid-category: service
solid-spec: [SPEC-069]
solid-description: Selects the governing declaration scope from its enclosing lexical scopes.
"""


class SourceScopeKindResolver(SourceSyntaxParsing[list[SourceScope], SourceScopeKind]):
    def __init__(
        self,
        priority: tuple[SourceScopeKind, ...] = (
            SourceScopeKind.CALLABLE,
            SourceScopeKind.CLOSURE,
            SourceScopeKind.TYPE,
        ),
        fallback: SourceScopeKind = SourceScopeKind.FILE,
    ) -> None:
        self._priority = priority
        self._fallback = fallback

    def parse(self, source: list[SourceScope]) -> SourceScopeKind:
        return next(
            (
                kind
                for kind in self._priority
                if any(scope.kind is kind for scope in source)
            ),
            self._fallback,
        )

"""Tests configurable declaration-scope priority."""

import unittest

from source.analysis.declarations.source_scope import SourceScope
from source.analysis.declarations.source_scope_kind import SourceScopeKind
from source.analysis.declarations.source_scope_kind_resolver import SourceScopeKindResolver
from source.source_line_range import SourceLineRange


"""
solid-name: TestSourceScopeKindResolver
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies lexical scope classification preserves its default priority and supports replacement policy data.
"""
class TestSourceScopeKindResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = SourceScopeKindResolver()

    def test_callable_takes_precedence_over_closure_and_type(self) -> None:
        scopes = [self._scope(SourceScopeKind.TYPE), self._scope(SourceScopeKind.CLOSURE), self._scope(SourceScopeKind.CALLABLE)]
        self.assertEqual(self.sut.parse(scopes), SourceScopeKind.CALLABLE)

    def test_closure_takes_precedence_over_type(self) -> None:
        self.assertEqual(self.sut.parse([self._scope(SourceScopeKind.TYPE), self._scope(SourceScopeKind.CLOSURE)]), SourceScopeKind.CLOSURE)

    def test_type_is_selected_when_it_is_the_only_enclosing_kind(self) -> None:
        self.assertEqual(self.sut.parse([self._scope(SourceScopeKind.TYPE)]), SourceScopeKind.TYPE)

    def test_empty_scopes_fall_back_to_file(self) -> None:
        self.assertEqual(self.sut.parse([]), SourceScopeKind.FILE)

    def test_injected_priority_changes_selection_without_changing_the_parser(self) -> None:
        sut = SourceScopeKindResolver(priority=(SourceScopeKind.TYPE, SourceScopeKind.CALLABLE))
        self.assertEqual(sut.parse([self._scope(SourceScopeKind.CALLABLE), self._scope(SourceScopeKind.TYPE)]), SourceScopeKind.TYPE)

    def test_injected_fallback_handles_an_empty_collection(self) -> None:
        self.assertEqual(SourceScopeKindResolver(fallback=SourceScopeKind.TYPE).parse([]), SourceScopeKind.TYPE)

    def _scope(self, kind: SourceScopeKind) -> SourceScope:
        return SourceScope(identity=kind.value, kind=kind, name=kind.value, span=SourceLineRange(start=1, end=2))

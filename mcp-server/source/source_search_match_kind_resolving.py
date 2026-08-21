"""Defines evidence classification for one source-search term."""

from __future__ import annotations

from typing import Protocol

from source.repository_source_unit import RepositorySourceUnit
from source.source_search_match_kind import SourceSearchMatchKind


"""
solid-name: SourceSearchMatchKindResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for classifying the exact repository-unit evidence matched by one normalized term.
"""
class SourceSearchMatchKindResolving(Protocol):
    def resolve(
        self,
        unit: RepositorySourceUnit,
        normalized_term: str,
    ) -> SourceSearchMatchKind | None: ...

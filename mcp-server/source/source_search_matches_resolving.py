"""Defines typed match resolution for one repository source unit."""

from typing import Protocol

from source.repository_source_unit import RepositorySourceUnit
from source.source_search_match import SourceSearchMatch
from source.source_search_query import SourceSearchQuery


"""
solid-name: SourceSearchMatchesResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving auditable query matches from one immutable repository source unit.
"""
class SourceSearchMatchesResolving(Protocol):
    def resolve(
        self,
        unit: RepositorySourceUnit,
        queries: list[SourceSearchQuery],
    ) -> list[SourceSearchMatch]: ...

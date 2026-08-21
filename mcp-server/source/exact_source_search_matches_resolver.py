"""Resolves exact repository source matches with typed provenance."""

from source.repository_source_unit import RepositorySourceUnit
from source.source_search_match import SourceSearchMatch
from source.source_search_match_kind_resolving import (
    SourceSearchMatchKindResolving,
)
from source.source_search_matches_resolving import SourceSearchMatchesResolving
from source.source_search_query import SourceSearchQuery


"""
solid-name: ExactSourceSearchMatchesResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Preserves query identity and exact terms while resolving typed source-match evidence.
"""
class ExactSourceSearchMatchesResolver(SourceSearchMatchesResolving):
    def __init__(self, kind: SourceSearchMatchKindResolving) -> None:
        self._kind = kind

    def resolve(
        self,
        unit: RepositorySourceUnit,
        queries: list[SourceSearchQuery],
    ) -> list[SourceSearchMatch]:
        matches: list[SourceSearchMatch] = []
        for query in queries:
            resolved_terms: set[str] = set()
            for term in query.terms:
                term_identity = term.casefold()
                if term_identity in resolved_terms:
                    continue
                resolved_terms.add(term_identity)
                kind = self._kind.resolve(unit, term_identity)
                if kind is not None:
                    matches.append(SourceSearchMatch(
                        query_id=query.id,
                        term=term,
                        kind=kind,
                    ))
        return matches

"""Classifies exact source evidence for repository search terms."""

from __future__ import annotations

from source.source_search_evidence import SourceSearchEvidence
from source.source_search_match_kind import SourceSearchMatchKind
from source.source_search_match_kind_resolving import (
    SourceSearchMatchKindResolving,
)


"""
solid-name: ExactSourceSearchMatchKindResolver
solid-category: service
solid-spec: [SPEC-040, SPEC-060]
solid-description: Classifies exact filename, import, frontmatter, symbol, and content matches from source snapshots.
"""
class ExactSourceSearchMatchKindResolver(SourceSearchMatchKindResolving):
    def resolve(
        self,
        evidence: SourceSearchEvidence,
        normalized_term: str,
    ) -> SourceSearchMatchKind | None:
        if normalized_term in evidence.filename:
            return SourceSearchMatchKind.FILENAME
        if normalized_term in evidence.imports:
            return SourceSearchMatchKind.IMPORT
        if normalized_term in evidence.frontmatter:
            return SourceSearchMatchKind.FRONTMATTER
        if normalized_term in evidence.symbols:
            return SourceSearchMatchKind.SYMBOL
        if normalized_term in evidence.content:
            return SourceSearchMatchKind.CONTENT
        return None

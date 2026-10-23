"""Defines evidence classification for one source-search term."""

from __future__ import annotations

from typing import Protocol

from source.source_search_evidence import SourceSearchEvidence
from source.source_search_match_kind import SourceSearchMatchKind

"""
solid-name: SourceSearchMatchKindResolving
solid-category: abstraction
solid-spec: [SPEC-040, SPEC-060]
solid-description: Contract for classifying the exact repository-unit evidence matched by one normalized term.
"""


class SourceSearchMatchKindResolving(Protocol):
    def resolve(
        self,
        evidence: SourceSearchEvidence,
        normalized_term: str,
    ) -> SourceSearchMatchKind | None: ...

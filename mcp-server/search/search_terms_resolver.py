"""Validates and normalizes codebase-search terms."""

from __future__ import annotations

from search.search_term_extracting import SearchTermExtracting


"""
solid-name: SearchTermsResolver
solid-category: service
solid-description: Validates codebase-search input forms and produces individual searchable terms.
"""
class SearchTermsResolver:
    def __init__(self, term_extractor: SearchTermExtracting) -> None:
        self._term_extractor = term_extractor

    def resolve(
        self,
        query: str | None,
        tags: list[str] | None,
    ) -> list[str]:
        if query is not None and tags is not None:
            raise ValueError("provide query or tags, not both.")
        if query is not None:
            terms = self._term_extractor.extract(query)
            if not terms:
                raise ValueError("query must contain at least one searchable term.")
            return terms
        if tags is None:
            return []

        terms: list[str] = []
        for tag in tags:
            normalized = tag.strip()
            if not normalized:
                raise ValueError("tags must not contain empty values.")
            if any(character.isspace() for character in normalized):
                raise ValueError(
                    "each tags entry must be one term; use query for a space-separated search."
                )
            terms.append(normalized)
        return terms

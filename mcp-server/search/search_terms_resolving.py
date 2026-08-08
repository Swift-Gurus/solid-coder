"""Defines normalization of codebase-search terms."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: SearchTermsResolving
solid-category: abstraction
solid-description: Contract for validating and normalizing codebase-search inputs into individual terms.
"""
class SearchTermsResolving(Protocol):
    def resolve(
        self,
        query: str | None,
        tags: list[str] | None,
    ) -> list[str]: ...

"""Defines extraction of searchable terms from a query."""

from typing import Protocol


"""
solid-name: SearchTermExtracting
solid-category: abstraction
solid-description: Contract for extracting individual searchable terms from a query.
"""
class SearchTermExtracting(Protocol):
    def extract(self, query: str) -> list[str]: ...

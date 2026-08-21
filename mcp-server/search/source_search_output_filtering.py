"""Defines source-search candidate threshold filtering."""

from typing import Protocol

from source.source_search_output import SourceSearchOutput


"""
solid-name: SourceSearchOutputFiltering
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for applying codebase-search eligibility policy to typed source candidates.
"""
class SourceSearchOutputFiltering(Protocol):
    def filter(
        self,
        output: SourceSearchOutput,
        minimum_matches: int,
    ) -> SourceSearchOutput: ...

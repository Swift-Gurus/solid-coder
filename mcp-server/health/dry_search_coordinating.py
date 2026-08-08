"""Defines validated DRY-search coordination."""

from typing import Optional, Protocol


"""
solid-name: DrySearchCoordinating
solid-category: abstraction
solid-description: Contract for validating codebase searches and recording successful health-check completion.
"""
class DrySearchCoordinating(Protocol):
    def search(
        self,
        sources_dir: Optional[str] = None,
        plan_path: Optional[str] = None,
        query: Optional[str] = None,
        tags: Optional[list[str]] = None,
        spec_numbers: Optional[list[str]] = None,
        min_matches: int = 3,
        output_dir: Optional[str] = None,
    ) -> str: ...

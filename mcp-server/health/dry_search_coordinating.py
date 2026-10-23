"""Defines validated DRY-search coordination."""

from typing import Protocol

"""
solid-name: DrySearchCoordinating
solid-category: abstraction
solid-description: Contract for validating codebase searches and recording successful health-check completion.
"""


class DrySearchCoordinating(Protocol):
    def search(
        self,
        sources_dir: str | None = None,
        plan_path: str | None = None,
        query: str | None = None,
        tags: list[str] | None = None,
        spec_numbers: list[str] | None = None,
        min_matches: int = 1,
        output_dir: str | None = None,
    ) -> str: ...

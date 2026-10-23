"""Defines tag-based codebase search used by boundary coordinators."""

from typing import Protocol

"""
solid-name: TagCodebaseSearching
solid-category: abstraction
solid-description: Contract for searching codebase metadata by normalized terms and specification identifiers.
"""


class TagCodebaseSearching(Protocol):
    def search(
        self,
        sources_dir: str | None = None,
        plan_path: str | None = None,
        tags: list | None = None,
        spec_numbers: list | None = None,
        min_matches: int = 3,
    ) -> str: ...

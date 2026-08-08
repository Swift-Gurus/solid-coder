"""Defines tag-based codebase search used by boundary coordinators."""

from typing import Optional, Protocol


"""
solid-name: TagCodebaseSearching
solid-category: abstraction
solid-description: Contract for searching codebase metadata by normalized terms and specification identifiers.
"""
class TagCodebaseSearching(Protocol):
    def search(
        self,
        sources_dir: Optional[str] = None,
        plan_path: Optional[str] = None,
        tags: Optional[list] = None,
        spec_numbers: Optional[list] = None,
        min_matches: int = 3,
    ) -> str: ...

"""Defines codebase-search boundary input translation."""

from typing import Optional, Protocol

from search.codebase_search_input_resolution import CodebaseSearchInputResolution


"""
solid-name: CodebaseSearchInputBuilding
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for translating codebase-search arguments into validated source-search input.
"""
class CodebaseSearchInputBuilding(Protocol):
    def build(
        self,
        sources_dir: Optional[str],
        plan_path: Optional[str],
        tags: Optional[list[str]],
        spec_numbers: Optional[list[str]],
        min_matches: int,
    ) -> CodebaseSearchInputResolution: ...

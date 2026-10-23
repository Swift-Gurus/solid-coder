"""Defines codebase-search boundary input translation."""

from typing import Protocol

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
        sources_dir: str | None,
        plan_path: str | None,
        tags: list[str] | None,
        spec_numbers: list[str] | None,
        min_matches: int,
    ) -> CodebaseSearchInputResolution: ...

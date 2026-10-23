"""Defines shared typed codebase-search execution."""

from typing import Protocol

from search.codebase_search_execution import CodebaseSearchExecution

"""
solid-name: CodebaseSearchExecuting
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for executing a filtered typed source search from codebase-search arguments.
"""


class CodebaseSearchExecuting(Protocol):
    def execute(
        self,
        sources_dir: str | None,
        plan_path: str | None,
        tags: list[str] | None,
        spec_numbers: list[str] | None,
        min_matches: int,
    ) -> CodebaseSearchExecution: ...

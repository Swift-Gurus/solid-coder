"""Defines shared typed codebase-search execution."""

from typing import Optional, Protocol

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
        sources_dir: Optional[str],
        plan_path: Optional[str],
        tags: Optional[list[str]],
        spec_numbers: Optional[list[str]],
        min_matches: int,
    ) -> CodebaseSearchExecution: ...

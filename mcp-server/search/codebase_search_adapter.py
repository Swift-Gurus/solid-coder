"""Adapts codebase-search calls to LLM-facing typed source-search results."""

from typing import Optional

from harness.flow_validation_error import FlowValidationError
from search.codebase_search_executing import CodebaseSearchExecuting
from search.codebase_search_output_rendering import CodebaseSearchOutputRendering


"""
solid-name: CodebaseSearchAdapter
solid-category: adapter
solid-spec: [SPEC-040]
solid-description: Returns reusable source units for LLM inspection through the codebase-search boundary.
"""
class CodebaseSearchAdapter:

    def __init__(
        self,
        executor: CodebaseSearchExecuting,
        renderer: CodebaseSearchOutputRendering,
    ) -> None:
        self._executor = executor
        self._renderer = renderer

    def search(
        self,
        sources_dir: Optional[str] = None,
        plan_path: Optional[str] = None,
        tags: Optional[list[str]] = None,
        spec_numbers: Optional[list[str]] = None,
        min_matches: int = 3,
    ) -> str:
        try:
            execution = self._executor.execute(
                sources_dir,
                plan_path,
                tags,
                spec_numbers,
                min_matches,
            )
        except (FlowValidationError, OSError, ValueError) as error:
            return f"Error: {error}"
        return self._renderer.render(
            execution.output,
            execution.project_root,
        )

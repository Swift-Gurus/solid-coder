"""Adapts codebase-search calls to LLM-facing typed source-search results."""

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
        sources_dir: str | None = None,
        plan_path: str | None = None,
        tags: list[str] | None = None,
        spec_numbers: list[str] | None = None,
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

"""Adapts codebase-search calls to CLI-compatible typed source-search data."""

from harness.flow_validation_error import FlowValidationError

from search.codebase_search_executing import CodebaseSearchExecuting
from search.codebase_search_output_serializing import CodebaseSearchOutputSerializing

"""
solid-name: RawCodebaseSearchAdapter
solid-category: adapter
solid-spec: [SPEC-040]
solid-description: Returns typed source-search results at the CLI JSON boundary.
"""


class RawCodebaseSearchAdapter:
    def __init__(
        self,
        executor: CodebaseSearchExecuting,
        serializer: CodebaseSearchOutputSerializing,
    ) -> None:
        self._executor = executor
        self._serializer = serializer

    def search_raw(
        self,
        sources_dir: str | None = None,
        plan_path: str | None = None,
        tags: list[str] | None = None,
        spec_numbers: list[str] | None = None,
        min_matches: int = 1,
    ) -> dict:
        try:
            execution = self._executor.execute(
                sources_dir,
                plan_path,
                tags,
                spec_numbers,
                min_matches,
            )
        except (FlowValidationError, OSError, ValueError) as error:
            return {"error": str(error), "matches": []}
        return self._serializer.serialize(execution.output)

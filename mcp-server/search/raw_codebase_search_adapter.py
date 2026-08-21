"""Adapts codebase-search calls to CLI-compatible typed source-search data."""

from typing import Optional

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
        sources_dir: Optional[str] = None,
        plan_path: Optional[str] = None,
        tags: Optional[list[str]] = None,
        spec_numbers: Optional[list[str]] = None,
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

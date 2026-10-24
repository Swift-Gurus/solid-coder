"""Composes the CLI-facing codebase-search boundary."""

from harness.project_context import ProjectDirectoryReading

from search.codebase_search_executor_factory import CodebaseSearchExecutorFactory
from search.codebase_search_output_serializer import CodebaseSearchOutputSerializer
from search.raw_codebase_search_adapter import RawCodebaseSearchAdapter

"""
solid-name: RawCodebaseSearcherFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides production CLI-facing codebase search adapters.
"""


class RawCodebaseSearcherFactory:
    def make(
        self, project_directory: ProjectDirectoryReading | None = None
    ) -> RawCodebaseSearchAdapter:
        return RawCodebaseSearchAdapter(
            executor=CodebaseSearchExecutorFactory().make(project_directory),
            serializer=CodebaseSearchOutputSerializer(),
        )

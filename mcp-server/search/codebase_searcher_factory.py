"""Composes the LLM-facing codebase-search boundary."""

from harness.project_context import ProjectDirectoryReading

from search.codebase_search_adapter import CodebaseSearchAdapter
from search.codebase_search_adapter_factory import (
    CodebaseSearchAdapterCreating,
    CodebaseSearchAdapterFactory,
)
from search.file_searcher import FileSearcher
from search.project_file_search_factory import (
    ProjectFileSearchCreating,
    ProjectFileSearchFactory,
)

_DEFAULT_ADAPTER_FACTORY: CodebaseSearchAdapterCreating = CodebaseSearchAdapterFactory()
_DEFAULT_FILE_SEARCH_FACTORY: ProjectFileSearchCreating = ProjectFileSearchFactory()

"""
solid-name: CodebaseSearcherFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Coordinates construction of codebase search adapters and project-scoped file search capabilities.
"""


class CodebaseSearcherFactory:
    def __init__(
        self,
        adapters: CodebaseSearchAdapterCreating = _DEFAULT_ADAPTER_FACTORY,
        file_search: ProjectFileSearchCreating = _DEFAULT_FILE_SEARCH_FACTORY,
    ) -> None:
        self._adapters = adapters
        self._file_search = file_search

    def make(
        self, project_directory: ProjectDirectoryReading | None = None
    ) -> CodebaseSearchAdapter:
        return self._adapters.make(project_directory)

    def make_file_search(
        self, project_directory: ProjectDirectoryReading
    ) -> FileSearcher:
        return self._file_search.make_file_search(project_directory)

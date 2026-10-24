"""Composes the presented codebase-search capability."""

from typing import Protocol

from harness.project_context import ProjectDirectoryReading

from search.codebase_search_adapter import CodebaseSearchAdapter
from search.codebase_search_executor_factory import CodebaseSearchExecutorFactory
from search.codebase_search_output_renderer import CodebaseSearchOutputRenderer

"""
solid-name: CodebaseSearchAdapterCreating
solid-category: abstraction
solid-spec: [SPEC-071]
solid-description: Contract for constructing the presented codebase-search boundary.
"""


class CodebaseSearchAdapterCreating(Protocol):
    def make(
        self, project_directory: ProjectDirectoryReading | None = None
    ) -> CodebaseSearchAdapter: ...


"""
solid-name: CodebaseSearchAdapterFactory
solid-category: factory
solid-spec: [SPEC-071]
solid-description: Composes the presented codebase-search adapter from shared search execution and text rendering capabilities.
"""


class CodebaseSearchAdapterFactory(CodebaseSearchAdapterCreating):
    def make(
        self, project_directory: ProjectDirectoryReading | None = None
    ) -> CodebaseSearchAdapter:
        return CodebaseSearchAdapter(
            executor=CodebaseSearchExecutorFactory().make(project_directory),
            renderer=CodebaseSearchOutputRenderer(),
        )

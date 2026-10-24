"""Composes the presented codebase-search capability."""

from typing import Protocol

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
    def make(self) -> CodebaseSearchAdapter: ...


"""
solid-name: CodebaseSearchAdapterFactory
solid-category: factory
solid-spec: [SPEC-071]
solid-description: Composes the presented codebase-search adapter from shared search execution and text rendering capabilities.
"""


class CodebaseSearchAdapterFactory(CodebaseSearchAdapterCreating):
    def make(self) -> CodebaseSearchAdapter:
        return CodebaseSearchAdapter(
            executor=CodebaseSearchExecutorFactory().make(),
            renderer=CodebaseSearchOutputRenderer(),
        )

"""Composes the LLM-facing codebase-search boundary."""

from search.codebase_search_adapter import CodebaseSearchAdapter
from search.codebase_search_executor_factory import CodebaseSearchExecutorFactory
from search.codebase_search_output_renderer import CodebaseSearchOutputRenderer


"""
solid-name: CodebaseSearcherFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides production LLM-facing codebase search adapters.
"""
class CodebaseSearcherFactory:
    def make(self) -> CodebaseSearchAdapter:
        return CodebaseSearchAdapter(
            executor=CodebaseSearchExecutorFactory().make(),
            renderer=CodebaseSearchOutputRenderer(),
        )

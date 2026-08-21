"""Composes the CLI-facing codebase-search boundary."""

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
    def make(self) -> RawCodebaseSearchAdapter:
        return RawCodebaseSearchAdapter(
            executor=CodebaseSearchExecutorFactory().make(),
            serializer=CodebaseSearchOutputSerializer(),
        )

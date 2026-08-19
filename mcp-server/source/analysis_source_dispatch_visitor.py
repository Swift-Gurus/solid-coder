"""Dispatches sealed analysis-source variants to focused resolvers."""

from source.analysis_source_visitor import AnalysisSourceVisitor
from source.file_analysis_source import FileAnalysisSource
from source.file_analysis_source_resolving import FileAnalysisSourceResolving
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.text_analysis_source import TextAnalysisSource
from source.text_analysis_source_resolving import TextAnalysisSourceResolving


"""
solid-name: AnalysisSourceDispatchVisitor
solid-category: service
solid-spec: [SPEC-040]
solid-description: Dispatches each sealed analysis-source variant to its focused resolver.
"""
class AnalysisSourceDispatchVisitor(
    AnalysisSourceVisitor[ResolvedAnalysisSource]
):
    def __init__(
        self,
        file_resolver: FileAnalysisSourceResolving,
        text_resolver: TextAnalysisSourceResolving,
    ) -> None:
        self._file_resolver = file_resolver
        self._text_resolver = text_resolver

    def visit_file(
        self,
        source: FileAnalysisSource,
    ) -> ResolvedAnalysisSource:
        return self._file_resolver.resolve(source)

    def visit_text(
        self,
        source: TextAnalysisSource,
    ) -> ResolvedAnalysisSource:
        return self._text_resolver.resolve(source)

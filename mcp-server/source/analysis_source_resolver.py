"""Resolves typed analysis sources through sealed variant dispatch."""

from source.analysis_source_resolving import AnalysisSourceResolving
from source.analysis_source_visitor import AnalysisSourceVisitor
from source.analyze_source_input import AnalyzeSourceInput
from source.resolved_analysis_source import ResolvedAnalysisSource


"""
solid-name: AnalysisSourceResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Delegates normalized analysis-source resolution through sealed variant dispatch.
"""
class AnalysisSourceResolver(AnalysisSourceResolving):
    def __init__(
        self,
        visitor: AnalysisSourceVisitor[ResolvedAnalysisSource],
    ) -> None:
        self._visitor = visitor

    def resolve(
        self,
        analysis_input: AnalyzeSourceInput,
    ) -> ResolvedAnalysisSource:
        return analysis_input.source.accept(self._visitor)

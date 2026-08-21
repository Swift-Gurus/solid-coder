"""Composes deterministic source-analysis operation dependencies."""

from source.analysis_source_resolver_factory import AnalysisSourceResolverFactory
from source.resolved_source_analyzer_factory import ResolvedSourceAnalyzerFactory
from source.source_analysis_operation import SourceAnalysisOperation


"""
solid-name: SourceAnalysisOperationFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Composes deterministic file and text source-analysis capabilities.
"""
class SourceAnalysisOperationFactory:
    def make(self) -> SourceAnalysisOperation:
        return SourceAnalysisOperation(
            source_resolver=AnalysisSourceResolverFactory().make(),
            analyzer=ResolvedSourceAnalyzerFactory().make(),
        )

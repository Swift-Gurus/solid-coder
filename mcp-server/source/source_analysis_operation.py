"""Coordinates typed deterministic source analysis."""

from source.analysis_source_resolving import AnalysisSourceResolving
from source.analyze_source_input import AnalyzeSourceInput
from source.resolved_source_analyzing import ResolvedSourceAnalyzing
from source.source_analysis import SourceAnalysis


"""
solid-name: SourceAnalysisOperation
solid-category: service
solid-spec: [SPEC-040]
solid-description: Analyzes a selected source input and returns deterministic source-analysis results, including unsupported-language outcomes.
"""
class SourceAnalysisOperation:
    def __init__(
        self,
        source_resolver: AnalysisSourceResolving,
        analyzer: ResolvedSourceAnalyzing,
    ) -> None:
        self._source_resolver = source_resolver
        self._analyzer = analyzer

    def execute(self, analysis_input: AnalyzeSourceInput) -> SourceAnalysis:
        source = self._source_resolver.resolve(analysis_input)
        return self._analyzer.analyze(source)

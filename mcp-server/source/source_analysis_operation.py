"""Coordinates typed deterministic source analysis."""

from source.analysis_source_resolving import AnalysisSourceResolving
from source.analyze_source_input import AnalyzeSourceInput
from source.language_source_analyzer_resolving import (
    LanguageSourceAnalyzerResolving,
)
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_language_detecting import SourceLanguageDetecting


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
        language_detector: SourceLanguageDetecting,
        analyzer_resolver: LanguageSourceAnalyzerResolving,
    ) -> None:
        self._source_resolver = source_resolver
        self._language_detector = language_detector
        self._analyzer_resolver = analyzer_resolver

    def execute(self, analysis_input: AnalyzeSourceInput) -> SourceAnalysis:
        source = self._source_resolver.resolve(analysis_input)
        language = self._language_detector.detect(source)
        analyzer = self._analyzer_resolver.resolve(language)
        if analyzer is None:
            return SourceAnalysis(
                source_identity=source.identity,
                language=language,
                decision=SourceAnalysisDecision.WHOLE_FILE_UNSUPPORTED,
            )
        return analyzer.analyze(source)

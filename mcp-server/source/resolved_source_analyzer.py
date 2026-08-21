"""Analyzes one resolved immutable source."""

from source.language_source_analyzer_resolving import (
    LanguageSourceAnalyzerResolving,
)
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.resolved_source_analyzing import ResolvedSourceAnalyzing
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_language_detecting import SourceLanguageDetecting
from source.whole_document_unit_resolving import WholeDocumentUnitResolving


"""
solid-name: ResolvedSourceAnalyzer
solid-category: service
solid-spec: [SPEC-040]
solid-description: Selects deterministic parsed or whole-document analysis for normalized immutable source content.
"""
class ResolvedSourceAnalyzer(ResolvedSourceAnalyzing):
    def __init__(
        self,
        language_detector: SourceLanguageDetecting,
        analyzer_resolver: LanguageSourceAnalyzerResolving,
        document_unit_resolver: WholeDocumentUnitResolving,
    ) -> None:
        self._language_detector = language_detector
        self._analyzer_resolver = analyzer_resolver
        self._document_unit_resolver = document_unit_resolver

    def analyze(self, source: ResolvedAnalysisSource) -> SourceAnalysis:
        language = self._language_detector.detect(source)
        analyzer = self._analyzer_resolver.resolve(language)
        if analyzer is None:
            return SourceAnalysis(
                source_identity=source.identity,
                file_extension=source.file_extension,
                decision=SourceAnalysisDecision.WHOLE_FILE_UNSUPPORTED,
                units=[self._document_unit_resolver.resolve(source)],
            )
        return analyzer.analyze(source)

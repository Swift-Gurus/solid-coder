"""Builds typed source analysis from one Swift parser execution."""

from source.language_source_analyzing import LanguageSourceAnalyzing
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_operation_error import SourceOperationError
from source.swift_ast_unit_decoding import SwiftASTUnitDecoding
from source.swift_parse_diagnostics_resolving import SwiftParseDiagnosticsResolving
from source.swift_parser_running import SwiftParserRunning
from source.swift_tag_detecting import SwiftTagDetecting


"""
solid-name: SwiftSourceAnalyzer
solid-category: service
solid-spec: [SPEC-040]
solid-description: Produces typed Swift source units and recoverable parse diagnostics from normalized content.
"""
class SwiftSourceAnalyzer(LanguageSourceAnalyzing):
    def __init__(
        self,
        parser: SwiftParserRunning,
        units: SwiftASTUnitDecoding,
        diagnostics: SwiftParseDiagnosticsResolving,
        tag_detector: SwiftTagDetecting,
    ) -> None:
        self._parser = parser
        self._units = units
        self._diagnostics = diagnostics
        self._tag_detector = tag_detector

    def analyze(self, source: ResolvedAnalysisSource) -> SourceAnalysis:
        result = self._parser.run(source.text)
        if result.timed_out:
            raise SourceOperationError("Swift source parsing timed out")
        if not result.stdout.strip():
            raise SourceOperationError(
                f"Swift source parsing produced no syntax tree: {result.stderr.strip()}"
            )
        units = self._units.decode(result.stdout, source.text)
        diagnostics = self._diagnostics.resolve(
            result.exit_code,
            result.stderr,
            units,
        )
        return SourceAnalysis(
            source_identity=source.identity,
            file_extension=source.file_extension,
            decision=(
                SourceAnalysisDecision.PARTIAL
                if diagnostics
                else SourceAnalysisDecision.PARSED
            ),
            diagnostics=diagnostics,
            units=units,
            detections=self._tag_detector.detect(
                result.stdout,
                source,
                units,
            ),
        )

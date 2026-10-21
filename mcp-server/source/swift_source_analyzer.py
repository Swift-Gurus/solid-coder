"""Builds typed source analysis from one Swift parser execution."""

from source.analysis.source_syntax_inventory import SourceSyntaxInventory
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.language_source_analyzing import LanguageSourceAnalyzing
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.swift_tag_detector import SwiftTagDetecting


"""
solid-name: SwiftSourceAnalyzer
solid-category: service
solid-spec: [SPEC-040, SPEC-063]
solid-description: Produces Swift declaration, type-inspection and technology facts with explicit parse completeness and recoverable diagnostics.
"""
class SwiftSourceAnalyzer(LanguageSourceAnalyzing):
    def __init__(
        self,
        parser: SourceSyntaxParsing[str, SourceSyntaxInventory],
        tag_detector: SwiftTagDetecting,
    ) -> None:
        self._parser = parser
        self._tag_detector = tag_detector

    def analyze(self, source: ResolvedAnalysisSource) -> SourceAnalysis:
        inventory = self._parser.parse(source.text)
        return SourceAnalysis(
            source_identity=source.identity,
            file_extension=source.file_extension,
            decision=(
                SourceAnalysisDecision.PARTIAL
                if inventory.diagnostics
                else SourceAnalysisDecision.PARSED
            ),
            diagnostics=inventory.diagnostics,
            units=inventory.units,
            declarations=inventory.declarations,
            type_inspections=inventory.type_inspections,
            calls=inventory.calls,
            detections=self._tag_detector.detect(inventory, source),
        )

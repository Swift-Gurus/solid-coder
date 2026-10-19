"""Language selection preserves the shared type-inspection contract."""

import unittest
from unittest.mock import Mock

from gate.dict_extension_lookup import DictExtensionLookup
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.analysis.type_inspections.source_type_inspection_kind import SourceTypeInspectionKind
from source.language_source_analyzer_registration import LanguageSourceAnalyzerRegistration
from source.language_source_analyzer_resolver import LanguageSourceAnalyzerResolver
from source.language_source_analyzing import LanguageSourceAnalyzing
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.resolved_source_analyzer import ResolvedSourceAnalyzer
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_language_detector import SourceLanguageDetector
from source.source_line_range import SourceLineRange
from source.whole_document_unit_resolver import WholeDocumentUnitResolver


"""
solid-name: TestTypeInspectionLanguageSelection
solid-category: unit-test
solid-spec: [SPEC-063]
solid-description: Verifies language-selected strategies publish shared inspection facts without invoking unrelated language analyzers.
"""
class TestTypeInspectionLanguageSelection(unittest.TestCase):
    def test_another_registered_language_returns_shared_facts_without_swift_analysis(self) -> None:
        swift = Mock(spec=LanguageSourceAnalyzing)
        alternate = Mock(spec=LanguageSourceAnalyzing)
        source = ResolvedAnalysisSource(
            identity="example.custom", file_extension=".custom", text="value as Widget",
        )
        expected = SourceAnalysis(
            source_identity=source.identity,
            file_extension=source.file_extension,
            decision=SourceAnalysisDecision.PARSED,
            type_inspections=[SourceTypeInspection(
                identity="inspection:0:15",
                kind=SourceTypeInspectionKind.CONVERSION,
                expression=source.text,
                operand="value",
                target_tokens=["Widget"],
                span=SourceLineRange(start=1, end=1),
                start_offset=0,
                end_offset=15,
            )],
        )
        alternate.analyze.return_value = expected
        analyzer = ResolvedSourceAnalyzer(
            language_detector=SourceLanguageDetector(DictExtensionLookup({
                ".swift": "swift", ".custom": "alternate",
            })),
            analyzer_resolver=LanguageSourceAnalyzerResolver([
                LanguageSourceAnalyzerRegistration(language="swift", analyzer=swift),
                LanguageSourceAnalyzerRegistration(language="alternate", analyzer=alternate),
            ]),
            document_unit_resolver=WholeDocumentUnitResolver(),
        )

        actual = analyzer.analyze(source)

        self.assertEqual(actual, expected)
        alternate.analyze.assert_called_once_with(source)
        swift.analyze.assert_not_called()
        self.assertEqual(SourceAnalysis.model_validate_json(actual.model_dump_json()), expected)

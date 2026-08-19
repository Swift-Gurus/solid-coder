"""Defines the typed deterministic source-analysis contract."""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from source.analyze_source_input import AnalyzeSourceInput
from source.file_analysis_source import FileAnalysisSource
from findings.review_unit_kind import ReviewUnitKind
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource


class TestSourceAnalysisOperation(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()
        self.swift = textwrap.dedent(
            """
            import SwiftUI

            class Controller {
                func nestedMethod() {}
            }
            struct DashboardView: View {
                var body: some View { Text("Dashboard") }
            }
            enum Status { case ready }
            protocol Loading {}
            actor Store {}
            extension DashboardView {}
            func makeFeature() -> DashboardView { DashboardView() }
            """
        ).lstrip()

    def test_file_and_equivalent_text_produce_the_same_analysis(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "Feature.swift"
        path.write_text(self.swift, encoding="utf-8")

        file_result = self.operation.execute(
            AnalyzeSourceInput(source=FileAnalysisSource(path=path))
        )
        text_result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    text=self.swift,
                    virtual_path=str(path),
                    language_hint="swift",
                )
            )
        )

        self.assertEqual(file_result, text_result)

    def test_extracts_ordered_top_level_swift_units_with_inclusive_spans(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    text=self.swift,
                    virtual_path="Feature.swift",
                )
            )
        )

        self.assertEqual(result.language, "swift")
        self.assertEqual(result.decision, SourceAnalysisDecision.PARSED)
        self.assertEqual(
            [(unit.kind, unit.name, unit.span.start, unit.span.end) for unit in result.units],
            [
                (ReviewUnitKind.CLASS, "Controller", 3, 5),
                (ReviewUnitKind.STRUCT, "DashboardView", 6, 8),
                (ReviewUnitKind.ENUM, "Status", 9, 9),
                (ReviewUnitKind.PROTOCOL, "Loading", 10, 10),
                (ReviewUnitKind.ACTOR, "Store", 11, 11),
                (ReviewUnitKind.EXTENSION, "DashboardView", 12, 12),
                (ReviewUnitKind.FUNCTION, "makeFeature", 13, 13),
            ],
        )
        self.assertNotIn("nestedMethod", [unit.name for unit in result.units])
        self.assertEqual(len({unit.identity for unit in result.units}), 7)

    def test_partial_swift_returns_safe_units_and_parse_diagnostics(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    text="struct Complete {}\nclass Broken {\n",
                    virtual_path="Partial.swift",
                )
            )
        )

        self.assertEqual(result.decision, SourceAnalysisDecision.PARTIAL)
        self.assertEqual(
            [(unit.name, unit.span.start, unit.span.end) for unit in result.units],
            [("Complete", 1, 1), ("Broken", 2, 2)],
        )
        self.assertTrue(result.diagnostics)
        self.assertEqual(result.diagnostics[0].line, 2)

    def test_unsupported_language_returns_explicit_whole_file_decision(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    text="class Feature:\n    pass\n",
                    virtual_path="feature.py",
                )
            )
        )

        self.assertEqual(result.language, "python")
        self.assertEqual(
            result.decision,
            SourceAnalysisDecision.WHOLE_FILE_UNSUPPORTED,
        )
        self.assertEqual(result.units, [])
        self.assertEqual(result.diagnostics, [])


if __name__ == "__main__":
    unittest.main()

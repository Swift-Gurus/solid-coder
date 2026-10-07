"""Integration contract for the shared syntax parser in source.analyze."""

import unittest
from unittest.mock import patch

from source.analysis.tree_sitter_syntax_parser import TreeSitterSyntaxParser
from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: TestTreeSitterSourceAnalysis
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies that source analysis parses once and derives typed inventory and technology evidence from executable syntax.
"""
class TestTreeSitterSourceAnalysis(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()

    def test_analysis_uses_shared_parser_once_for_units_members_and_tags(self) -> None:
        source = "import SwiftUI\nstruct Card: View { var body: some View { Text(\"Hi\") } }\n"
        with patch.object(
            TreeSitterSyntaxParser,
            "parse",
            autospec=True,
            side_effect=TreeSitterSyntaxParser.parse,
        ) as parse:
            result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
                virtual_path="Card.swift", text=source,
            )))

        self.assertEqual(parse.call_count, 1)
        self.assertEqual(parse.call_args.args[1], source)
        self.assertEqual([unit.name for unit in result.units], ["Card"])
        self.assertEqual([member.name for member in result.units[0].members], ["body"])
        self.assertEqual([detection.tag for detection in result.detections], ["ui", "swiftui", "view"])

    def test_comments_and_literal_text_do_not_activate_technology_rules(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Labels.swift",
            text=(
                "// import SwiftUI; Task; actor; XCTest\n"
                "struct Labels {\n"
                '  let text = "await Sendable MainActor Testing XCUIApplication"\n'
                '  let raw = #"Task await Testing"#\n'
                "}\n"
            ),
        )))

        self.assertEqual(result.detections, [])

    def test_tag_evidence_points_to_code_not_an_earlier_unicode_comment(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift",
            text="// 😀 async\nstruct Store {\n  func load() async {}\n}\n",
        )))

        self.assertEqual(
            [detection.tag for detection in result.detections],
            ["concurrency", "structured-concurrency"],
        )
        self.assertTrue(all(detection.evidence[0].span.start == 3 for detection in result.detections))

    def test_code_inside_string_interpolation_still_activates_rules(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Message.swift",
            text='func message() -> String { "value: \\(Task.isCancelled)" }\n',
        )))

        self.assertEqual(
            [detection.tag for detection in result.detections],
            ["concurrency", "structured-concurrency"],
        )

    def test_multiple_property_bindings_keep_distinct_member_identities(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Coordinates.swift",
            text="public struct Coordinates { public private(set) var x = 1, y = 2 }\n",
        )))

        members = result.units[0].members
        self.assertEqual([member.name for member in members], ["x", "y"])
        self.assertEqual([member.visibility.value for member in members], ["public", "public"])
        self.assertEqual(len({member.identity for member in members}), 2)

"""Tests deterministic Swift tags used by executable review-rule matchers."""

import unittest

from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.technology_detection_scope import TechnologyDetectionScope
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: TestSwiftReviewRuleTagDetection
solid-category: unit-test
solid-spec: [SPEC-039, SPEC-040]
solid-description: Verifies deterministic activation tags for concurrency, Swift unit-test, and Swift UI-test rule workflows.
"""
class TestSwiftReviewRuleTagDetection(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()

    def test_detects_structured_concurrency_from_async_syntax(self) -> None:
        tags = self._file_tags(
            """
            actor ProfileStore {
                func load() async {
                    await refresh()
                }

                private func refresh() async {}
            }
            """
        )

        self.assertIn("concurrency", tags)
        self.assertIn("structured-concurrency", tags)

    def test_detects_swiftui_view_for_rule_activation(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    text="""
                    import SwiftUI

                    struct ProfileView: View {
                        var body: some View {
                            Text("Profile")
                        }
                    }
                    """,
                    virtual_path="ReviewTarget.swift",
                )
            )
        )
        file_tags = [
            detection.tag
            for detection in result.detections
            if detection.scope is TechnologyDetectionScope.FILE
        ]
        unit_tags = [
            detection.tag
            for detection in result.detections
            if detection.scope is TechnologyDetectionScope.UNIT
        ]

        self.assertIn("swiftui", file_tags)
        self.assertIn("view", unit_tags)

    def test_detects_swift_testing_as_unit_test(self) -> None:
        tags = self._file_tags(
            """
            import Testing

            @Test func loadsProfile() {
                #expect(true)
            }
            """
        )

        self.assertIn("testing", tags)
        self.assertIn("unit-test", tags)
        self.assertNotIn("ui-test", tags)

    def test_detects_xcui_application_as_ui_test(self) -> None:
        tags = self._file_tags(
            """
            import XCTest

            final class LoginUITests: XCTestCase {
                let app = XCUIApplication()
            }
            """
        )

        self.assertIn("testing", tags)
        self.assertIn("xctest", tags)
        self.assertIn("ui-test", tags)
        self.assertNotIn("unit-test", tags)

    def _file_tags(self, source: str) -> list[str]:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    text=source,
                    virtual_path="ReviewTarget.swift",
                )
            )
        )
        return [
            detection.tag
            for detection in result.detections
            if detection.scope is TechnologyDetectionScope.FILE
        ]

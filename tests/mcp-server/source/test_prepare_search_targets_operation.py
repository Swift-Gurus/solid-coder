"""Tests deterministic preparation of immutable source-search targets."""

from __future__ import annotations

import sys
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from findings.review_unit_kind import ReviewUnitKind
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import (
    PrepareSearchTargetsOperationFactory,
)
from source.search_target_granularity import SearchTargetGranularity
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: TestPrepareSearchTargetsOperation
solid-category: unit-test
solid-spec: [SPEC-040]
solid-description: Verifies MCP-owned file and unit search targets contain stable identity, exact code, deterministic terms, and exclusions.
"""
class TestPrepareSearchTargetsOperation(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = PrepareSearchTargetsOperationFactory().make()
        self.source_text = textwrap.dedent(
            """
            import SwiftUI

            struct UserLoader {
                func load() {}
            }

            struct DashboardView: View {
                var body: some View { Text("Dashboard") }
            }
            """
        ).lstrip()
        self.source = TextAnalysisSource(
            text=self.source_text,
            virtual_path="Sources/Feature.swift",
        )

    def test_unit_granularity_returns_ordered_exact_source_slices(self) -> None:
        result = self.operation.execute(PrepareSearchTargetsInput(
            source=self.source,
            granularity=SearchTargetGranularity.UNIT,
        ))

        self.assertEqual(
            [target.name for target in result.targets],
            ["UserLoader", "DashboardView"],
        )
        self.assertEqual(
            [target.kind for target in result.targets],
            [ReviewUnitKind.STRUCT, ReviewUnitKind.STRUCT],
        )
        self.assertEqual(
            result.targets[0].code,
            "struct UserLoader {\n    func load() {}\n}",
        )
        self.assertEqual(
            result.targets[1].code,
            "struct DashboardView: View {\n"
            "    var body: some View { Text(\"Dashboard\") }\n"
            "}",
        )
        self.assertEqual(
            [target.identity for target in result.targets],
            [
                f"{Path('Sources/Feature.swift').resolve()}#struct:UserLoader:3",
                f"{Path('Sources/Feature.swift').resolve()}#struct:DashboardView:7",
            ],
        )
        self.assertEqual(
            [target.unit_identity for target in result.targets],
            ["struct:UserLoader:3", "struct:DashboardView:7"],
        )
        self.assertIn("userloader", result.targets[0].deterministic_terms)
        self.assertIn("swiftui", result.targets[0].deterministic_terms)
        self.assertIn("view", result.targets[1].deterministic_terms)

    def test_file_granularity_returns_one_complete_document_target(self) -> None:
        result = self.operation.execute(PrepareSearchTargetsInput(
            source=self.source,
            granularity=SearchTargetGranularity.FILE,
        ))

        self.assertEqual(len(result.targets), 1)
        target = result.targets[0]
        self.assertEqual(target.code, self.source_text)
        self.assertEqual(target.kind, ReviewUnitKind.DOCUMENT)
        self.assertEqual(target.name, "Feature.swift")
        self.assertEqual(
            target.identity,
            f"{Path('Sources/Feature.swift').resolve()}#document",
        )
        self.assertIn("feature", target.deterministic_terms)
        self.assertIn("swiftui", target.deterministic_terms)


if __name__ == "__main__":
    unittest.main()

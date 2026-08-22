"""Tests typed repository source search for workflow-owned comparison."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_query import SourceSearchQuery
from source.source_unit_identity import SourceUnitIdentity
from source.search_target_granularity import SearchTargetGranularity


"""
solid-name: TestSourceSearchOperation
solid-category: unit-test
solid-spec: [SPEC-040]
solid-description: Validates typed repository search provenance, exclusions, ordering, and query validation.
"""
class TestSourceSearchOperation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self._write(
            "Sources/Current.swift",
            "struct InvoiceTaxCalculator {}\n",
        )
        self._write(
            "Sources/InvoiceTaxCalculator.swift",
            """
            // solid-name: InvoiceTaxCalculator
            // solid-description: Calculates invoice tax totals.
            import Foundation
            struct InvoiceTaxCalculator {
                func calculateInvoiceTax() {}
            }
            """,
        )
        self._write(
            "Sources/TaxReport.swift",
            "struct TaxReport { let invoice: String }\n",
        )
        self.operation = SourceSearchOperationFactory().make(
            lambda: self.project_root,
            SearchTargetGranularity.UNIT,
        )

    def test_returns_stable_candidates_with_query_and_match_provenance(self) -> None:
        result = self.operation.execute(SourceSearchInput(
            queries=[
                SourceSearchQuery(
                    id="invoice-tax",
                    terms=["InvoiceTaxCalculator", "Foundation", "invoice"],
                )
            ],
            excluded_units=[SourceUnitIdentity(
                source_identity="Sources/Current.swift",
                unit_identity="struct:InvoiceTaxCalculator:1",
            )],
        ))

        self.assertEqual(
            [candidate.source_identity for candidate in result.candidates],
            [
                "Sources/InvoiceTaxCalculator.swift",
                "Sources/TaxReport.swift",
            ],
        )
        documented = result.candidates[0]
        self.assertEqual(documented.unit, "InvoiceTaxCalculator")
        self.assertEqual(
            documented.description,
            "Calculates invoice tax totals.",
        )
        self.assertEqual(
            documented.path,
            (self.project_root / "Sources/InvoiceTaxCalculator.swift").resolve(),
        )
        undocumented = result.candidates[1]
        self.assertEqual(undocumented.unit, "TaxReport")
        self.assertEqual(
            undocumented.description,
            "No solid-description frontmatter.",
        )
        self.assertEqual(
            undocumented.path,
            (self.project_root / "Sources/TaxReport.swift").resolve(),
        )
        first_matches = result.candidates[0].matches
        self.assertEqual({match.query_id for match in first_matches}, {"invoice-tax"})
        self.assertEqual(
            {match.term for match in first_matches},
            {"InvoiceTaxCalculator", "Foundation", "invoice"},
        )
        self.assertNotIn(
            "Sources/Current.swift",
            [candidate.source_identity for candidate in result.candidates],
        )

    def test_rejects_a_delimiter_encoded_search_term(self) -> None:
        with self.assertRaises(ValidationError):
            SourceSearchQuery(id="invoice-tax", terms=["invoice tax"])

    def test_returns_only_the_frontmatter_unit_that_matches_the_query(self) -> None:
        self._write(
            "Sources/Combined.swift",
            """
            // solid-name: DateFormatter
            // solid-description: Formats dates for display.
            struct DateFormatter {}

            // solid-name: PaymentAuthorizer
            // solid-description: Authorizes invoice payments.
            struct PaymentAuthorizer {}
            """,
        )

        result = self.operation.execute(SourceSearchInput(
            queries=[SourceSearchQuery(id="payment", terms=["PaymentAuthorizer"])],
        ))

        combined = [
            candidate
            for candidate in result.candidates
            if candidate.path.name == "Combined.swift"
        ]
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined[0].unit, "PaymentAuthorizer")
        self.assertEqual(
            combined[0].description,
            "Authorizes invoice payments.",
        )

    def test_does_not_publish_a_symlink_that_resolves_outside_the_project(self) -> None:
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        outside_path = Path(outside.name) / "Escaped.swift"
        outside_path.write_text("struct Escaped {}\n", encoding="utf-8")
        (self.project_root / "Escaped.swift").symlink_to(outside_path)

        result = self.operation.execute(SourceSearchInput(
            queries=[SourceSearchQuery(id="escaped", terms=["Escaped"])],
        ))

        self.assertEqual(result.candidates, [])

    def _write(self, relative_path: str, content: str) -> None:
        destination = self.project_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

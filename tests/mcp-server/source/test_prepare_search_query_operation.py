"""Tests deterministic assembly of one target-owned source-search query."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from findings.review_unit_kind import ReviewUnitKind
from source.prepare_search_query_input import PrepareSearchQueryInput
from source.prepare_search_query_operation import PrepareSearchQueryOperation
from source.source_line_range import SourceLineRange
from source.source_search_target import SourceSearchTarget


"""
solid-name: TestPrepareSearchQueryOperation
solid-category: unit-test
solid-spec: [SPEC-040]
solid-description: Verifies model-generated terms are validated and deterministically merged into an MCP-owned target query.
"""
class TestPrepareSearchQueryOperation(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = PrepareSearchQueryOperation()
        self.target = SourceSearchTarget(
            identity="struct:UserLoader:1",
            source_identity="Sources/UserLoader.swift",
            name="UserLoader",
            kind=ReviewUnitKind.STRUCT,
            span=SourceLineRange(start=1, end=3),
            code="struct UserLoader {}",
            deterministic_terms=["userloader", "swiftui"],
        )

    def test_merges_normalizes_and_deduplicates_terms_in_stable_order(self) -> None:
        result = self.operation.execute(PrepareSearchQueryInput(
            target=self.target,
            generated_terms=["Fetcher", "userloader", "Retriever", "fetcher"],
            excluded_source_identities=["Sources/UserLoader.swift"],
        ))

        self.assertEqual(len(result.queries), 1)
        query = result.queries[0]
        self.assertEqual(query.id, "struct:UserLoader:1")
        self.assertEqual(
            query.terms,
            ["userloader", "swiftui", "fetcher", "retriever"],
        )
        self.assertEqual(
            result.excluded_source_identities,
            ["Sources/UserLoader.swift"],
        )

    def test_rejects_delimiter_encoded_or_whitespace_terms_at_input(self) -> None:
        for invalid_term in ["remote loader", "loader,fetcher", "loader;fetcher"]:
            with self.subTest(invalid_term=invalid_term):
                with self.assertRaises(ValidationError):
                    PrepareSearchQueryInput(
                        target=self.target,
                        generated_terms=[invalid_term],
                    )

    def test_preserves_stable_target_identity_when_project_path_has_spaces(self) -> None:
        target = self.target.model_copy(update={
            "identity": "/tmp/My Project/UserLoader.swift#struct:UserLoader:1"
        })

        result = self.operation.execute(PrepareSearchQueryInput(
            target=target,
            generated_terms=["fetcher"],
        ))

        self.assertEqual(result.queries[0].id, target.identity)


if __name__ == "__main__":
    unittest.main()

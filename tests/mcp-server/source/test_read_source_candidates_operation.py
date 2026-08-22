"""Tests bounded, root-confined loading of typed source-search candidates."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from source.candidate_source_read_kind import CandidateSourceReadKind
from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.read_source_candidates_operation_factory import (
    ReadSourceCandidatesOperationFactory,
)
from source.source_search_candidate import SourceSearchCandidate
from source.source_candidate_origin import SourceCandidateOrigin
from source.source_search_input import SourceSearchInput
from source.source_search_match import SourceSearchMatch
from source.source_search_match_kind import SourceSearchMatchKind
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_query import SourceSearchQuery
from source.search_target_granularity import SearchTargetGranularity


"""
solid-name: TestReadSourceCandidatesOperation
solid-category: unit-test
solid-spec: [SPEC-040]
solid-description: Validates bounded candidate loading, root confinement, and changed-source audit outcomes.
"""
class TestReadSourceCandidatesOperation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.candidate_path = self.project_root / "Sources" / "TaxRule.swift"
        self.candidate_path.parent.mkdir(parents=True)
        self.candidate_path.write_text(
            "struct TaxRule { let invoice: String }\n",
            encoding="utf-8",
        )
        self.candidate = SourceSearchOperationFactory().make(
            lambda: self.project_root,
            SearchTargetGranularity.UNIT,
        ).execute(
            SourceSearchInput(
                queries=[SourceSearchQuery(id="tax", terms=["TaxRule"])],
            )
        ).candidates[0]
        self.operation = ReadSourceCandidatesOperationFactory(
            lambda: self.project_root
        ).make()

    def test_loads_bounded_content_with_the_search_candidate_provenance(self) -> None:
        result = self.operation.execute(ReadSourceCandidatesInput(
            candidates=[self.candidate],
            max_bytes_per_candidate=12,
        ))

        loaded = result.results[0]
        self.assertEqual(loaded.kind, CandidateSourceReadKind.LOADED)
        self.assertEqual(loaded.candidate, self.candidate)
        self.assertEqual(loaded.content, "struct TaxRu")
        self.assertTrue(loaded.truncated)

    def test_reports_a_changed_candidate_instead_of_reading_new_bytes(self) -> None:
        self.candidate_path.write_text("struct Changed {}\n", encoding="utf-8")

        result = self.operation.execute(ReadSourceCandidatesInput(
            candidates=[self.candidate],
        ))

        self.assertEqual(result.results[0].kind, CandidateSourceReadKind.CHANGED)

    def test_reports_an_escaped_root_candidate_as_a_typed_outcome(self) -> None:
        escaped = SourceSearchCandidate(
            unit="Outside.swift",
            unit_identity="document:Outside.swift:1",
            description="No solid-description frontmatter.",
            path=(self.project_root.parent / "Outside.swift").resolve(),
            source_identity="../Outside.swift",
            start_offset=0,
            end_offset=1,
            content_sha256="0" * 64,
            origin=SourceCandidateOrigin.REPOSITORY,
            matches=[SourceSearchMatch(
                query_id="outside",
                term="Outside",
                kind=SourceSearchMatchKind.FILENAME,
            )],
        )

        result = self.operation.execute(ReadSourceCandidatesInput(
            candidates=[escaped],
        ))

        self.assertEqual(result.results[0].kind, CandidateSourceReadKind.ESCAPED_ROOT)


if __name__ == "__main__":
    unittest.main()

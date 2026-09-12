"""Tests typed validation of LLM-selected source-candidate identities."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.project_context import ProjectDirectory
from source.search_target_granularity import SearchTargetGranularity
from source.source_candidate_selection import SourceCandidateSelection
from source.source_search_candidate import SourceSearchCandidate
from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_query import SourceSearchQuery
from source.validate_candidate_selection_input import ValidateCandidateSelectionInput
from source.validate_candidate_selection_operation import (
    ValidateCandidateSelectionOperation,
)


"""
solid-name: TestValidateCandidateSelectionOperation
solid-category: unit-test
solid-spec: [SPEC-039, SPEC-040]
solid-description: Verifies selected candidate identities resolve uniquely within discovered source candidates.
"""
class TestValidateCandidateSelectionOperation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        (self.project_root / "First.swift").write_text(
            "struct FirstFormatter { func format() {} }\n",
            encoding="utf-8",
        )
        (self.project_root / "Second.swift").write_text(
            "struct SecondFormatter { func format() {} }\n",
            encoding="utf-8",
        )
        self.candidates = SourceSearchOperationFactory().make(
            ProjectDirectory(path=self.project_root),
            SearchTargetGranularity.UNIT,
        ).execute(SourceSearchInput(
            queries=[SourceSearchQuery(id="format", terms=["Formatter"])],
        )).candidates
        self.operation = ValidateCandidateSelectionOperation()

    def test_returns_only_selected_candidates_in_selection_order(self) -> None:
        selections = [
            self._selection(self.candidates[1]),
            self._selection(self.candidates[0]),
        ]

        output = self.operation.execute(ValidateCandidateSelectionInput(
            candidates=self.candidates,
            selections=selections,
        ))

        self.assertEqual(
            output.selected_candidates,
            [self.candidates[1], self.candidates[0]],
        )

    def test_rejects_duplicate_selected_identity(self) -> None:
        selection = self._selection(self.candidates[0])

        with self.assertRaisesRegex(ValidationError, "duplicate reference"):
            ValidateCandidateSelectionInput(
                candidates=self.candidates,
                selections=[selection, selection],
            )

    def test_rejects_identity_that_search_did_not_return(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unknown reference"):
            ValidateCandidateSelectionInput(
                candidates=self.candidates,
                selections=[SourceCandidateSelection(
                    path="/missing/Missing.swift",
                    unit="Missing",
                    reasoning="The summary appeared relevant.",
                )],
            )

    @staticmethod
    def _selection(candidate: SourceSearchCandidate) -> SourceCandidateSelection:
        return SourceCandidateSelection(
            path=str(candidate.path),
            unit=candidate.unit,
            reasoning="The summary identifies matching formatting behavior.",
        )


if __name__ == "__main__":
    unittest.main()

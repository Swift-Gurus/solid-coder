"""Tests typed validation of LLM-selected source-candidate identities."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.project_context import ProjectDirectory
from source.selected_source_candidate import SelectedSourceCandidate
from source.source_candidate_disposition import SourceCandidateDisposition
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
        ).execute(SourceSearchInput(
            queries=[SourceSearchQuery(id="format", terms=["Formatter"])],
        )).candidates
        self.operation = ValidateCandidateSelectionOperation()

    def test_returns_inspected_candidates_in_discovered_order(self) -> None:
        dispositions = [
            self._disposition(2, "REJECT"),
            self._disposition(1, "INSPECT"),
        ]

        output = self.operation.execute(ValidateCandidateSelectionInput(
            candidates=self.candidates,
            dispositions=dispositions,
        ))

        self.assertEqual(
            output.selected_candidates,
            [SelectedSourceCandidate(
                candidate_id="candidate-1",
                source=self.candidates[0],
            )],
        )
        self.assertEqual(
            output.dispositions,
            [dispositions[1], dispositions[0]],
        )

    def test_rejects_duplicate_candidate_id(self) -> None:
        disposition = self._disposition(1, "INSPECT")

        with self.assertRaisesRegex(ValidationError, "duplicate candidate IDs.*candidate-1"):
            ValidateCandidateSelectionInput(
                candidates=self.candidates,
                dispositions=[disposition, disposition],
            )

    def test_rejects_unknown_candidate_id(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unknown candidate IDs.*candidate-3"):
            ValidateCandidateSelectionInput(
                candidates=self.candidates,
                dispositions=[
                    self._disposition(1, "REJECT"),
                    self._disposition(2, "REJECT"),
                    self._disposition(3, "REJECT"),
                ],
            )

    def test_rejects_missing_candidate_id(self) -> None:
        with self.assertRaisesRegex(ValidationError, "missing candidate IDs.*candidate-2"):
            ValidateCandidateSelectionInput(
                candidates=self.candidates,
                dispositions=[self._disposition(1, "INSPECT")],
            )

    def test_accepts_empty_dispositions_for_empty_search(self) -> None:
        output = self.operation.execute(ValidateCandidateSelectionInput(
            candidates=[],
            dispositions=[],
        ))

        self.assertEqual(output.selected_candidates, [])
        self.assertEqual(output.dispositions, [])

    @staticmethod
    def _disposition(
        candidate_index: int,
        disposition: str,
    ) -> SourceCandidateDisposition:
        return SourceCandidateDisposition(
            candidate_id=f"candidate-{candidate_index}",
            disposition=disposition,
            reasoning="The summary identifies matching formatting behavior.",
            evidence="The candidate description names formatting behavior.",
        )


if __name__ == "__main__":
    unittest.main()

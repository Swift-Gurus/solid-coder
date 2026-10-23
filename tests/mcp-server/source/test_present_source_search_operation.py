"""Tests the workflow-facing presentation of typed source-search results."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.project_context import ProjectDirectory
from search.codebase_search_output_renderer import CodebaseSearchOutputRenderer
from source.present_source_search_operation import PresentSourceSearchOperation
from source.source_candidate_origin import SourceCandidateOrigin
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)
from source.source_search_candidate import SourceSearchCandidate
from source.source_search_match import SourceSearchMatch
from source.source_search_match_kind import SourceSearchMatchKind
from source.source_search_results import SourceSearchResults

"""
solid-name: TestPresentSourceSearchOperation
solid-category: unit-test
solid-spec: [SPEC-039, SPEC-040]
solid-description: Verifies workflow source search exposes readable candidate summaries without internal search metadata.
"""


class TestPresentSourceSearchOperation(unittest.TestCase):
    def test_renders_candidate_id_name_description_and_path(self) -> None:
        candidate_path = Path("/project/Sources/ExistingCatalog.swift")
        output = PresentSourceSearchOperation(
            renderer=CodebaseSearchOutputRenderer(),
            project_directory=ProjectDirectory(path=Path("/project")),
        ).execute(
            SourceSearchResults(
                candidates=[
                    SourceSearchCandidate(
                        unit="ExistingCatalog",
                        unit_identity="class:ExistingCatalog:6",
                        description="Persists cached catalog data.",
                        path=candidate_path,
                        source_identity="Sources/ExistingCatalog.swift",
                        content_sha256="a" * 64,
                        origin=SourceCandidateOrigin.REPOSITORY,
                        matches=[
                            SourceSearchMatch(
                                query_id="catalog",
                                term="catalog",
                                kind=SourceSearchMatchKind.FILENAME,
                            )
                        ],
                    )
                ],
                files_scanned=4,
            )
        )

        self.assertEqual(
            output.text,
            "Here is what we found:\n\n"
            "candidate_id: candidate-1\n"
            "unit: ExistingCatalog\n"
            "description: Persists cached catalog data.\n"
            f"path: {candidate_path}",
        )
        self.assertNotIn("source_identity", output.text)
        self.assertNotIn("unit_identity", output.text)
        self.assertNotIn("content_sha256", output.text)
        self.assertNotIn("matches", output.text)

    def test_registered_presentation_accepts_existing_workflow_input(self) -> None:
        registration = next(
            registration
            for registration in SourceOperationRegistrationsFactory(
                project_directory=ProjectDirectory(path=Path("/project")),
            ).make()
            if registration.name == "source.present_search"
        )

        operation_input = registration.input_model.model_validate(
            {
                "candidates": [],
                "files_scanned": 4,
            }
        )
        output = registration.handler.execute(operation_input)

        self.assertEqual(
            output.text,
            "No files matched in /project (4 files scanned).",
        )


if __name__ == "__main__":
    unittest.main()

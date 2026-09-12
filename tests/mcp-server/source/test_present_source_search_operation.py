"""Tests the workflow-facing presentation of typed source-search results."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.project_context import ProjectDirectory  # noqa: E402
from search.codebase_search_output_renderer import CodebaseSearchOutputRenderer  # noqa: E402
from source.present_source_search_operation import PresentSourceSearchOperation  # noqa: E402
from source.source_candidate_origin import SourceCandidateOrigin  # noqa: E402
from source.source_search_candidate import SourceSearchCandidate  # noqa: E402
from source.source_search_match import SourceSearchMatch  # noqa: E402
from source.source_search_match_kind import SourceSearchMatchKind  # noqa: E402
from source.source_search_output import SourceSearchOutput  # noqa: E402


"""
solid-name: TestPresentSourceSearchOperation
solid-category: unit-test
solid-spec: [SPEC-039, SPEC-040]
solid-description: Verifies workflow source search exposes readable candidate summaries without internal search metadata.
"""
class TestPresentSourceSearchOperation(unittest.TestCase):
    def test_renders_only_candidate_name_description_and_path(self) -> None:
        candidate_path = Path("/project/Sources/ExistingCatalog.swift")
        output = PresentSourceSearchOperation(
            renderer=CodebaseSearchOutputRenderer(),
            project_directory=ProjectDirectory(path=Path("/project")),
        ).execute(SourceSearchOutput(
            candidates=[SourceSearchCandidate(
                unit="ExistingCatalog",
                unit_identity="class:ExistingCatalog:6",
                description="Persists cached catalog data.",
                path=candidate_path,
                source_identity="Sources/ExistingCatalog.swift",
                start_offset=10,
                end_offset=100,
                content_sha256="a" * 64,
                origin=SourceCandidateOrigin.REPOSITORY,
                matches=[SourceSearchMatch(
                    query_id="catalog",
                    term="catalog",
                    kind=SourceSearchMatchKind.FILENAME,
                )],
            )],
            files_scanned=4,
        ))

        self.assertEqual(
            output.text,
            "Here is what we found:\n\n"
            "unit: ExistingCatalog\n"
            "description: Persists cached catalog data.\n"
            f"path: {candidate_path}",
        )
        self.assertNotIn("source_identity", output.text)
        self.assertNotIn("unit_identity", output.text)
        self.assertNotIn("content_sha256", output.text)
        self.assertNotIn("matches", output.text)


if __name__ == "__main__":
    unittest.main()

"""Verifies the controlled source project used by review comparisons."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HARNESS = Path(__file__).resolve().parents[1]
if str(_HARNESS) not in sys.path:
    sys.path.insert(0, str(_HARNESS))

from review_comparison_source_project import (  # noqa: E402
    ReviewComparisonSourceProject,
)


class TestReviewComparisonSourceProject(unittest.TestCase):

    def test_materializes_only_the_locked_source_files(self) -> None:
        project = ReviewComparisonSourceProject.create()
        self.addCleanup(project.cleanup)

        source_paths = sorted(
            path.relative_to(project.root).as_posix()
            for path in project.root.rglob("*.swift")
        )

        self.assertEqual(
            source_paths,
            [
                "Sources/Candidates/ExistingCatalog.swift",
                "Sources/Candidates/ExistingCatalogServing.swift",
                "Sources/ReviewTarget.swift",
            ],
        )
        self.assertEqual(
            project.review_target,
            project.root / "Sources" / "ReviewTarget.swift",
        )


if __name__ == "__main__":
    unittest.main()

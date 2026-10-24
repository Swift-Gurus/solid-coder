"""Checks search summary totals independently of candidate selection."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.project_context import ProjectDirectory
from search.raw_codebase_searcher_factory import RawCodebaseSearcherFactory
from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_query import SourceSearchQuery

"""
solid-name: TestCodebaseSearchSummary
solid-category: unit-test
solid-spec: [SPEC-040]
solid-description: Verifies search scan totals remain distinct from matched units, eligibility thresholds, and candidate limits.
"""


class TestCodebaseSearchSummary(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        GitWorkingTreeFixture(self.root).initialize()
        (self.root / "Combined.swift").write_text(
            "// solid-name: Alpha\n"
            "// solid-description: Shared alpha work.\n"
            "struct Alpha {}\n\n"
            "// solid-name: Beta\n"
            "// solid-description: Shared beta work.\n"
            "struct Beta {}\n",
            encoding="utf-8",
        )
        (self.root / "Other.swift").write_text(
            "// solid-name: Other\n"
            "// solid-description: Shared other work.\n"
            "struct Other {}\n",
            encoding="utf-8",
        )
        (self.root / "Plain.swift").write_text("struct Plain {}\n", encoding="utf-8")
        directory = patch(
            "search.codebase_search_executor_factory._resolve_project_root",
            return_value=self.root,
        )
        directory.start()
        self.addCleanup(directory.stop)
        self.searcher = RawCodebaseSearcherFactory().make()

    def test_scan_summary_includes_documented_files_that_do_not_match(self) -> None:
        result = self.searcher.search_raw(sources_dir=str(self.root), tags=["alpha"])

        self.assertEqual(
            result["summary"],
            {
                "total_files_scanned": 3,
                "files_with_frontmatter": 2,
                "files_matched": 1,
            },
        )

    def test_no_matches_preserves_scan_summary(self) -> None:
        result = self.searcher.search_raw(sources_dir=str(self.root), tags=["absent"])

        self.assertEqual(result["matches"], [])
        self.assertEqual(result["summary"]["files_with_frontmatter"], 2)

    def test_threshold_filter_does_not_change_scan_summary(self) -> None:
        result = self.searcher.search_raw(
            sources_dir=str(self.root),
            tags=["shared"],
            min_matches=2,
        )

        self.assertEqual(result["matches"], [])
        self.assertEqual(result["summary"]["files_with_frontmatter"], 2)

    def test_multiple_matching_units_count_as_one_matched_file(self) -> None:
        result = self.searcher.search_raw(
            sources_dir=str(self.root), tags=["alpha", "beta"]
        )

        self.assertEqual(
            [match["unit"] for match in result["matches"]], ["Alpha", "Beta"]
        )
        self.assertEqual(result["summary"]["files_matched"], 1)

    def test_candidate_limit_does_not_change_scan_summary(self) -> None:
        operation = SourceSearchOperationFactory().make(
            ProjectDirectory(path=self.root),
        )

        result = operation.execute(
            SourceSearchInput(
                queries=[SourceSearchQuery(id="shared", terms=["shared"])],
                max_candidates=1,
            )
        )

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.files_scanned, 3)
        self.assertEqual(result.files_with_frontmatter, 2)

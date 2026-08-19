"""Tests deterministic collection of Git working-tree changes."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from source.collect_changes_input import CollectChangesInput
from source.collect_changes_operation_factory import CollectChangesOperationFactory
from source.source_change_kind import SourceChangeKind
from source.source_operation_error import SourceOperationError
from git_working_tree_fixture import GitWorkingTreeFixture


"""
solid-name: TestCollectChangesOperation
solid-category: unit-test
solid-spec: [SPEC-040]
solid-description: Validates deterministic typed Git working-tree change collection.
"""
class TestCollectChangesOperation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.git = GitWorkingTreeFixture(self.project_root)
        self.git.initialize()
        self.git.write("Modified.swift", "one\ntwo\n")
        self.git.write("Deleted.swift", "delete me\n")
        self.git.write("Old.swift", "one\ntwo\nthree\nfour\n")
        self.git.run("add", ".")
        self.git.run("commit", "-m", "initial")

    def test_collects_all_working_tree_change_kinds_in_stable_path_order(self) -> None:
        self.git.write("Modified.swift", "one\ntwo\nstaged\n")
        self.git.run("add", "Modified.swift")
        self.git.write("Modified.swift", "one\ntwo\nstaged\nunstaged\n")
        self.git.remove("Deleted.swift")
        self.git.run("mv", "Old.swift", "Renamed.swift")
        self.git.write(
            "Renamed.swift",
            "one\ntwo\nthree\nfour\nrenamed addition\n",
        )
        self.git.write("Untracked.swift", "first\nsecond\n")

        result = CollectChangesOperationFactory().make().execute(
            CollectChangesInput(project_root=str(self.project_root))
        )

        self.assertEqual(
            [change.path for change in result.files],
            [
                "Deleted.swift",
                "Modified.swift",
                "Renamed.swift",
                "Untracked.swift",
            ],
        )
        deleted = next(change for change in result.files if change.path == "Deleted.swift")
        modified = next(change for change in result.files if change.path == "Modified.swift")
        renamed = next(change for change in result.files if change.path == "Renamed.swift")
        untracked = next(change for change in result.files if change.path == "Untracked.swift")
        self.assertEqual(deleted.kind, SourceChangeKind.DELETED)
        self.assertEqual(modified.kind, SourceChangeKind.MODIFIED)
        self.assertEqual(modified.added_ranges[0].start, 3)
        self.assertEqual(modified.added_ranges[0].end, 4)
        self.assertEqual(renamed.kind, SourceChangeKind.RENAMED)
        self.assertEqual(renamed.previous_path, "Old.swift")
        self.assertEqual(renamed.added_ranges[0].start, 5)
        self.assertEqual(renamed.added_ranges[0].end, 5)
        self.assertEqual(untracked.kind, SourceChangeKind.ADDED)
        self.assertEqual(untracked.added_ranges[0].start, 1)
        self.assertEqual(untracked.added_ranges[0].end, 2)

    def test_clean_repository_returns_an_empty_typed_collection(self) -> None:
        result = CollectChangesOperationFactory().make().execute(
            CollectChangesInput(project_root=str(self.project_root))
        )

        self.assertEqual(result.files, [])

    def test_collection_does_not_mutate_the_working_tree(self) -> None:
        self.git.write("Modified.swift", "one\ntwo\nchanged\n")
        self.git.write("Untracked.swift", "new\n")
        before = self.git.output("status", "--porcelain=v1", "-z")

        CollectChangesOperationFactory().make().execute(
            CollectChangesInput(project_root=str(self.project_root))
        )

        after = self.git.output("status", "--porcelain=v1", "-z")
        self.assertEqual(after, before)

    def test_git_failure_identifies_the_project_and_query_purpose(self) -> None:
        non_repository_directory = tempfile.TemporaryDirectory()
        self.addCleanup(non_repository_directory.cleanup)
        non_repository = Path(non_repository_directory.name)

        with self.assertRaises(SourceOperationError) as raised:
            CollectChangesOperationFactory().make().execute(
                CollectChangesInput(project_root=str(non_repository))
            )

        self.assertIn(str(non_repository), str(raised.exception))
        self.assertIn("collecting tracked additions", str(raised.exception))

if __name__ == "__main__":
    unittest.main()

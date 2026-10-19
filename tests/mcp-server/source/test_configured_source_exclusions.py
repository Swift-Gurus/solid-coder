"""Repository discovery honors the same project exclusions as the write gate."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from harness.project_context import ProjectDirectory
from source.filtered_repository_source_files_discoverer import FilteredRepositorySourceFilesDiscoverer
from source.os_directory_tree_walker import OsDirectoryTreeWalker
from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_query import SourceSearchQuery


class TestConfiguredSourceExclusions(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="source-exclusions-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".git").mkdir()
        (self.root / ".solid-coder").mkdir()
        (self.root / ".solid-coder" / "config.toml").write_text(
            '[hooks.pre_write_gate]\nexclude = ["Vendor/**/*.swift"]\n'
        )
        (self.root / "Vendor").mkdir()
        self.excluded = self.root / "Vendor" / "Catalog.swift"
        self.excluded.write_text("struct Catalog {}")
        self.included = self.root / "Catalog.swift"
        self.included.write_text("struct Catalog {}")
        self.nonmatching = self.root / "Vendor" / "Catalog.json"
        self.nonmatching.write_text("{}")

    def test_configured_exclusions_apply_before_snapshot_reads(self):
        files = FilteredRepositorySourceFilesDiscoverer(
            tree=OsDirectoryTreeWalker(), excluded_directories=frozenset({".git", ".solid-coder"}),
        ).discover(self.root)
        self.assertEqual(files, sorted([self.included, self.nonmatching]))

    def test_production_source_search_does_not_return_excluded_candidates(self):
        result = SourceSearchOperationFactory().make(ProjectDirectory(path=self.root)).execute(
            SourceSearchInput(queries=[SourceSearchQuery(id="catalog", terms=["Catalog"])])
        )
        self.assertEqual([candidate.path for candidate in result.candidates], [self.included])
        self.assertEqual(result.files_scanned, 1)

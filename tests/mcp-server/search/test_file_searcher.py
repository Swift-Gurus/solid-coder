"""Checks local-model name search without starting a model."""

import tempfile
import unittest
from pathlib import Path

from harness.path_builder import PathBuilder
from harness.project_context import ProjectDirectory
from search.file_searcher import FileSearcher
from search.codebase_searcher_factory import CodebaseSearcherFactory
from source.default_repository_source_exclusions import DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES
from source.filtered_repository_source_files_discoverer import FilteredRepositorySourceFilesDiscoverer
from source.os_directory_tree_walker import OsDirectoryTreeWalker
from utils.path_file_system_reader import PathFileSystemReader


"""
solid-name: TestFileSearcher
solid-category: unit-test
solid-spec: [SPEC-060]
solid-description: Verifies injected definition and filename discovery preserves local-model tool responses and source exclusions.
"""
class TestFileSearcher(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.path = self.root / "Catalog.swift"
        self.path.write_text("struct Catalog {}\nstruct CatalogExtra {}\nextension Catalog {}\n")
        (self.root / "Catalog.json").write_text("struct Catalog {}")
        hidden = self.root / ".build"
        hidden.mkdir()
        (hidden / "Catalog.swift").write_text("struct Catalog {}")
        self.search = FileSearcher(
            files=FilteredRepositorySourceFilesDiscoverer(
                tree=OsDirectoryTreeWalker(),
                excluded_directories=DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES,
            ),
            file_system=PathFileSystemReader(),
            project_directory=ProjectDirectory(path=self.root),
            paths=PathBuilder(),
        )

    def test_definition_search_preserves_lines_and_excludes_resources_and_builds(self) -> None:
        self.assertEqual(self.search.grep_by_name("Catalog"),
                         f"{self.path}:1: struct Catalog {{}}\n{self.path}:3: extension Catalog {{}}")

    def test_filename_search_preserves_globs_and_excludes_builds(self) -> None:
        self.assertEqual(self.search.glob_by_name("*Catalog*.swift"), str(self.path))

    def test_missing_directory_is_reported_for_both_tools(self) -> None:
        missing = str(self.root / "missing")
        self.assertEqual(self.search.grep_by_name("Catalog", missing), f"Error: directory not found: {missing}")
        self.assertEqual(self.search.glob_by_name("*Catalog*", missing), f"Error: directory not found: {missing}")

    def test_no_matches_preserve_tool_messages(self) -> None:
        self.assertEqual(self.search.grep_by_name("Absent"), "No definitions or extensions of 'Absent' found.")
        self.assertEqual(self.search.glob_by_name("*Absent*"), "No files matching '*Absent*' found.")

    def test_production_factory_preserves_the_configured_project(self) -> None:
        search = CodebaseSearcherFactory().make_file_search(ProjectDirectory(path=self.root))

        self.assertEqual(search.glob_by_name("*Catalog*.swift"), str(self.path))
        self.assertEqual(search.grep_by_name("Catalog"), self.search.grep_by_name("Catalog"))

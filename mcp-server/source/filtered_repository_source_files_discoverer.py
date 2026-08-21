"""Discovers repository source files with a configured exclusion policy."""

from pathlib import Path

from source.directory_tree_walking import DirectoryTreeWalking
from source.repository_source_files_discovering import (
    RepositorySourceFilesDiscovering,
)


"""
solid-name: FilteredRepositorySourceFilesDiscoverer
solid-category: service
solid-spec: [SPEC-040]
solid-description: Discovers stable project file paths after applying configured directory exclusions.
"""
class FilteredRepositorySourceFilesDiscoverer(RepositorySourceFilesDiscovering):
    def __init__(
        self,
        tree: DirectoryTreeWalking,
        excluded_directories: frozenset[str],
    ) -> None:
        self._tree = tree
        self._excluded_directories = excluded_directories

    def discover(self, project_root: Path) -> list[Path]:
        return sorted(self._tree.files(
            project_root,
            self._excluded_directories,
        ))

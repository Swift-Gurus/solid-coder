"""Discovers repository source files with a configured exclusion policy."""

from pathlib import Path

from gate.default_exclusion_checker_factory import DefaultExclusionCheckerFactory, ExclusionPolicyCreating
from source.directory_tree_walking import DirectoryTreeWalking
from source.repository_source_files_discovering import (
    RepositorySourceFilesDiscovering,
)


"""
solid-name: FilteredRepositorySourceFilesDiscoverer
solid-category: service
solid-spec: [SPEC-040, SPEC-064]
solid-description: Discovers stable project file paths after applying directory exclusions and effective project path policies before source content is read.
"""
class FilteredRepositorySourceFilesDiscoverer(RepositorySourceFilesDiscovering):
    def __init__(
        self,
        tree: DirectoryTreeWalking,
        excluded_directories: frozenset[str],
        exclusions: ExclusionPolicyCreating = DefaultExclusionCheckerFactory(),
    ) -> None:
        self._tree = tree
        self._excluded_directories = excluded_directories
        self._exclusions = exclusions

    def discover(self, project_root: Path) -> list[Path]:
        policy = self._exclusions.create(project_root)
        return sorted(
            path for path in self._tree.files(project_root, self._excluded_directories)
            if not policy.is_excluded(str(path)) and not policy.is_excluded(str(path.resolve()))
        )

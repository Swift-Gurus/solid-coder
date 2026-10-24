"""Composes production project-source file discovery."""

from typing import Protocol

from source.default_repository_source_exclusions import (
    DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES,
)
from source.filtered_repository_source_files_discoverer import (
    FilteredRepositorySourceFilesDiscoverer,
)
from source.os_directory_tree_walker import OsDirectoryTreeWalker
from source.repository_source_files_discovering import RepositorySourceFilesDiscovering

"""
solid-name: RepositorySourceFilesCreating
solid-category: abstraction
solid-spec: [SPEC-071]
solid-description: Contract for constructing project-source file discovery capabilities.
"""


class RepositorySourceFilesCreating(Protocol):
    def make(self) -> RepositorySourceFilesDiscovering: ...


"""
solid-name: RepositorySourceFilesFactory
solid-category: factory
solid-spec: [SPEC-071]
solid-description: Composes repository file discovery with the shared traversal and exclusion policy.
"""


class RepositorySourceFilesFactory(RepositorySourceFilesCreating):
    def make(self) -> RepositorySourceFilesDiscovering:
        return FilteredRepositorySourceFilesDiscoverer(
            tree=OsDirectoryTreeWalker(),
            excluded_directories=DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES,
        )

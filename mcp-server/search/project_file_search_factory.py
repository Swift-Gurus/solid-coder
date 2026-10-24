"""Composes project-scoped filename and type search."""

from typing import Protocol

from harness.project_context import ProjectDirectoryReading
from health.config.hc_config_core import find_repository_root
from source.repository_source_files_factory import RepositorySourceFilesFactory
from source.repository_target_resolver import RepositoryTargetResolver
from utils.path_file_system_reader import PathFileSystemReader

from search.file_searcher import FileSearcher

"""
solid-name: ProjectFileSearchCreating
solid-category: abstraction
solid-spec: [SPEC-071]
solid-description: Contract for constructing project-scoped filename and type search capabilities.
"""


class ProjectFileSearchCreating(Protocol):
    def make_file_search(
        self, project_directory: ProjectDirectoryReading
    ) -> FileSearcher: ...


"""
solid-name: ProjectFileSearchFactory
solid-category: factory
solid-spec: [SPEC-071]
solid-description: Composes project-scoped filename and type search with shared file discovery and repository target validation.
"""


class ProjectFileSearchFactory(ProjectFileSearchCreating):
    def make_file_search(
        self, project_directory: ProjectDirectoryReading
    ) -> FileSearcher:
        return FileSearcher(
            files=RepositorySourceFilesFactory().make(),
            file_system=PathFileSystemReader(),
            project_directory=project_directory,
            targets=RepositoryTargetResolver(find_repository_root),
        )

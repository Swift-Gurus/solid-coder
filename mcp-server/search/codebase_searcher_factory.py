"""Composes the LLM-facing codebase-search boundary."""

from harness.path_builder import PathBuilder
from harness.project_context import ProjectDirectoryReading
from search.codebase_search_adapter import CodebaseSearchAdapter
from search.codebase_search_executor_factory import CodebaseSearchExecutorFactory
from search.codebase_search_output_renderer import CodebaseSearchOutputRenderer
from search.file_searcher import FileSearcher
from source.default_repository_source_exclusions import DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES
from source.filtered_repository_source_files_discoverer import FilteredRepositorySourceFilesDiscoverer
from source.os_directory_tree_walker import OsDirectoryTreeWalker
from utils.path_file_system_reader import PathFileSystemReader


"""
solid-name: CodebaseSearcherFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides production LLM-facing codebase search adapters.
"""
class CodebaseSearcherFactory:
    def make(self) -> CodebaseSearchAdapter:
        return CodebaseSearchAdapter(
            executor=CodebaseSearchExecutorFactory().make(),
            renderer=CodebaseSearchOutputRenderer(),
        )

    def make_file_search(self, project_directory: ProjectDirectoryReading) -> FileSearcher:
        return FileSearcher(
            files=FilteredRepositorySourceFilesDiscoverer(
                tree=OsDirectoryTreeWalker(),
                excluded_directories=DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES,
            ),
            file_system=PathFileSystemReader(),
            project_directory=project_directory,
            paths=PathBuilder(),
        )

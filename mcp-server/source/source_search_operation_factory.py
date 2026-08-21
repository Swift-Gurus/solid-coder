"""Composes typed repository source search."""

from harness.sha256_content_hasher import Sha256ContentHasher
from source.default_repository_source_exclusions import (
    DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES,
)
from source.exact_source_search_match_kind_resolver import (
    ExactSourceSearchMatchKindResolver,
)
from source.exact_source_search_matches_resolver import (
    ExactSourceSearchMatchesResolver,
)
from source.exact_source_tokens_resolver import ExactSourceTokensResolver
from source.filtered_repository_source_files_discoverer import (
    FilteredRepositorySourceFilesDiscoverer,
)
from source.frontmatter_repository_source_units_resolver import (
    FrontmatterRepositorySourceUnitsResolver,
)
from source.os_directory_tree_walker import OsDirectoryTreeWalker
from source.repository_source_snapshots_collector import (
    RepositorySourceSnapshotsCollector,
)
from source.source_search_operation import SourceSearchOperation
from source.source_frontmatter_reader_factory import SourceFrontmatterReaderFactory

"""
solid-name: SourceSearchOperationFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides repository source search operations.
"""
class SourceSearchOperationFactory:
    def make(self) -> SourceSearchOperation:
        return SourceSearchOperation(
            snapshots=RepositorySourceSnapshotsCollector(
                files=FilteredRepositorySourceFilesDiscoverer(
                    tree=OsDirectoryTreeWalker(),
                    excluded_directories=(
                        DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES
                    ),
                ),
                content_hasher=Sha256ContentHasher(),
            ),
            units=FrontmatterRepositorySourceUnitsResolver(
                frontmatter_reader=SourceFrontmatterReaderFactory().make(),
            ),
            matches=ExactSourceSearchMatchesResolver(
                kind=ExactSourceSearchMatchKindResolver(
                    tokens=ExactSourceTokensResolver()
                )
            ),
        )

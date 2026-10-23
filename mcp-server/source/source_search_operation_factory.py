"""Composes typed repository source search."""

from harness.path_builder import PathBuilder
from harness.project_context import ProjectDirectoryReading
from harness.sha256_content_hasher import Sha256ContentHasher
from source.default_repository_source_exclusions import (
    DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES,
)
from source.exact_source_search_evidence_resolver import (
    ExactSourceSearchEvidenceResolver,
)
from source.exact_source_search_match_kind_resolver import (
    ExactSourceSearchMatchKindResolver,
)
from source.exact_source_search_matches_resolver import (
    ExactSourceSearchMatchesResolver,
)
from source.exact_source_tokens_resolver_factory import (
    ExactSourceTokensResolverFactory,
)
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
from source.repository_source_unit_projector import RepositorySourceUnitProjector
from source.source_frontmatter_reader_factory import SourceFrontmatterReaderFactory
from source.source_frontmatter_selector import SourceFrontmatterSelector
from source.source_search_operation import SourceSearchOperation
from source.source_unit_exclusion_checker import SourceUnitExclusionChecker
from source.utf8_source_slice_resolver import UTF8SourceSliceResolver
from source.whole_file_repository_source_unit_builder import (
    WholeFileRepositorySourceUnitBuilder,
)

"""
solid-name: SourceSearchOperationFactory
solid-category: factory
solid-spec: [SPEC-040, SPEC-060]
solid-description: Provides repository source search operations.
"""


class SourceSearchOperationFactory:
    def make(
        self,
        project_directory: ProjectDirectoryReading,
    ) -> SourceSearchOperation:
        frontmatter_reader = SourceFrontmatterReaderFactory().make()
        units = FrontmatterRepositorySourceUnitsResolver(
            frontmatter_reader=frontmatter_reader,
            unit_builder=WholeFileRepositorySourceUnitBuilder(),
            projector=RepositorySourceUnitProjector(
                frontmatter=SourceFrontmatterSelector(),
                source_slice=UTF8SourceSliceResolver(),
            ),
        )
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
            units=units,
            matches=ExactSourceSearchMatchesResolver(
                kind=ExactSourceSearchMatchKindResolver(),
                evidence=ExactSourceSearchEvidenceResolver(
                    tokens=ExactSourceTokensResolverFactory().make()
                ),
            ),
            exclusion=SourceUnitExclusionChecker(PathBuilder()),
            project_directory=project_directory,
        )

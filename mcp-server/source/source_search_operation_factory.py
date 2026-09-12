"""Composes typed repository source search."""

from pathlib import Path

from harness.path_builder import PathBuilder
from harness.project_context import ProjectDirectoryReading
from harness.sha256_content_hasher import Sha256ContentHasher
from source.analyzed_repository_source_units_resolver import (
    AnalyzedRepositorySourceUnitsResolver,
)
from source.default_repository_source_exclusions import (
    DEFAULT_REPOSITORY_SOURCE_EXCLUDED_DIRECTORIES,
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
from source.source_search_operation import SourceSearchOperation
from source.source_frontmatter_reader_factory import SourceFrontmatterReaderFactory
from source.repository_source_unit_projector import RepositorySourceUnitProjector
from source.resolved_source_analyzer_factory import ResolvedSourceAnalyzerFactory
from source.search_target_granularity import SearchTargetGranularity
from source.source_frontmatter_selector import SourceFrontmatterSelector
from source.source_unit_exclusion_checker import SourceUnitExclusionChecker
from source.utf8_source_slice_resolver import UTF8SourceSliceResolver
from source.whole_file_repository_source_unit_builder import (
    WholeFileRepositorySourceUnitBuilder,
)

"""
solid-name: SourceSearchOperationFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides repository source search operations.
"""
class SourceSearchOperationFactory:
    def make(
        self,
        project_directory: ProjectDirectoryReading,
        granularity: SearchTargetGranularity,
    ) -> SourceSearchOperation:
        frontmatter_reader = SourceFrontmatterReaderFactory().make()
        units = (
            AnalyzedRepositorySourceUnitsResolver(
                analyzer=ResolvedSourceAnalyzerFactory().make(),
                frontmatter_reader=frontmatter_reader,
                projector=RepositorySourceUnitProjector(
                    frontmatter=SourceFrontmatterSelector(),
                    source_slice=UTF8SourceSliceResolver(),
                ),
            )
            if granularity is SearchTargetGranularity.UNIT
            else FrontmatterRepositorySourceUnitsResolver(
                frontmatter_reader=frontmatter_reader,
                unit_builder=WholeFileRepositorySourceUnitBuilder(),
            )
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
                kind=ExactSourceSearchMatchKindResolver(
                    tokens=ExactSourceTokensResolverFactory().make()
                )
            ),
            exclusion=SourceUnitExclusionChecker(PathBuilder()),
            project_directory=project_directory,
        )

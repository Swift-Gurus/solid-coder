"""Builds source-search targets through registered granularity policy."""

from pathlib import Path

from harness.content_hashing import ContentHashing
from source.prepare_search_targets_output import PrepareSearchTargetsOutput
from source.repository_source_snapshot import RepositorySourceSnapshot
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.search_target_granularity import SearchTargetGranularity
from source.source_analysis import SourceAnalysis
from source.source_search_targets_building_resolving import (
    SourceSearchTargetsBuildingResolving,
)


"""
solid-name: SourceSearchTargetsBuilder
solid-category: service
solid-spec: [SPEC-040]
solid-description: Prepares source-search targets by selecting the policy appropriate to the requested granularity.
"""
class SourceSearchTargetsBuilder:
    def __init__(
        self,
        builders: SourceSearchTargetsBuildingResolving,
        content_hasher: ContentHashing,
    ) -> None:
        self._builders = builders
        self._content_hasher = content_hasher

    def build(
        self,
        source: ResolvedAnalysisSource,
        analysis: SourceAnalysis,
        granularity: SearchTargetGranularity,
    ) -> PrepareSearchTargetsOutput:
        builder = self._builders.resolve(granularity)
        return PrepareSearchTargetsOutput(
            targets=builder.build(source, analysis),
            snapshot=RepositorySourceSnapshot(
                path=Path(source.identity).resolve(),
                source_identity=source.identity,
                content=source.text,
                content_sha256=self._content_hasher.hash(
                    source.text.encode("utf-8")
                ),
            ),
        )

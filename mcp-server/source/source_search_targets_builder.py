"""Builds source-search targets through registered granularity policy."""

from source.prepare_search_targets_output import PrepareSearchTargetsOutput
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
solid-description: Builds reviewed-source search targets through an injected granularity capability and publishes exclusions.
"""
class SourceSearchTargetsBuilder:
    def __init__(
        self,
        builders: SourceSearchTargetsBuildingResolving,
    ) -> None:
        self._builders = builders

    def build(
        self,
        source: ResolvedAnalysisSource,
        analysis: SourceAnalysis,
        granularity: SearchTargetGranularity,
    ) -> PrepareSearchTargetsOutput:
        builder = self._builders.resolve(granularity)
        return PrepareSearchTargetsOutput(
            targets=builder.build(source, analysis),
            excluded_source_identities=[source.identity],
        )

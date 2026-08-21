"""Builds ordered parsed-unit source-search targets."""

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_analysis import SourceAnalysis
from source.source_search_target import SourceSearchTarget
from source.source_search_targets_building import SourceSearchTargetsBuilding
from source.source_unit_search_target_building import (
    SourceUnitSearchTargetBuilding,
)


"""
solid-name: UnitSourceSearchTargetsBuilder
solid-category: service
solid-spec: [SPEC-040]
solid-description: Prepares searchable targets for every ordered unit in a resolved source analysis.
"""
class UnitSourceSearchTargetsBuilder(SourceSearchTargetsBuilding):
    def __init__(self, target: SourceUnitSearchTargetBuilding) -> None:
        self._target = target

    def build(
        self,
        source: ResolvedAnalysisSource,
        analysis: SourceAnalysis,
    ) -> list[SourceSearchTarget]:
        return [
            self._target.build(source, analysis, unit)
            for unit in analysis.units
        ]

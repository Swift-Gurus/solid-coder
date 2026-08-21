"""Defines resolution of source-search target construction policy."""

from typing import Protocol

from source.search_target_granularity import SearchTargetGranularity
from source.source_search_targets_building import SourceSearchTargetsBuilding


"""
solid-name: SourceSearchTargetsBuildingResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving a target-construction capability from typed search granularity.
"""
class SourceSearchTargetsBuildingResolving(Protocol):
    def resolve(
        self,
        granularity: SearchTargetGranularity,
    ) -> SourceSearchTargetsBuilding: ...

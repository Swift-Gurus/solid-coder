"""Defines one source-search target builder registration."""

from dataclasses import dataclass

from source.search_target_granularity import SearchTargetGranularity
from source.source_search_targets_building import SourceSearchTargetsBuilding


"""
solid-name: SourceSearchTargetsBuilderRegistration
solid-category: model
solid-spec: [SPEC-040]
solid-description: Associates one typed search-target granularity with its construction capability.
"""
@dataclass(frozen=True)
class SourceSearchTargetsBuilderRegistration:
    granularity: SearchTargetGranularity
    builder: SourceSearchTargetsBuilding

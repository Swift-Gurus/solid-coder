"""Defines construction of one parsed-unit source-search target."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_analysis import SourceAnalysis
from source.source_search_target import SourceSearchTarget
from source.source_unit import SourceUnit


"""
solid-name: SourceUnitSearchTargetBuilding
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for preparing one searchable target from a resolved source unit and its analysis evidence.
"""
class SourceUnitSearchTargetBuilding(Protocol):
    def build(
        self,
        source: ResolvedAnalysisSource,
        analysis: SourceAnalysis,
        unit: SourceUnit,
    ) -> SourceSearchTarget: ...

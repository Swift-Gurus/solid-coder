"""Defines construction of search targets from one resolved source analysis."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_analysis import SourceAnalysis
from source.source_search_target import SourceSearchTarget


"""
solid-name: SourceSearchTargetsBuilding
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for one file-or-unit source-search target construction policy.
"""
class SourceSearchTargetsBuilding(Protocol):
    def build(
        self,
        source: ResolvedAnalysisSource,
        analysis: SourceAnalysis,
    ) -> list[SourceSearchTarget]: ...

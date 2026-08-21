"""Defines deterministic analysis of one resolved immutable source."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_analysis import SourceAnalysis


"""
solid-name: ResolvedSourceAnalyzing
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for analyzing normalized immutable source content without rereading its origin.
"""
class ResolvedSourceAnalyzing(Protocol):
    def analyze(self, source: ResolvedAnalysisSource) -> SourceAnalysis: ...

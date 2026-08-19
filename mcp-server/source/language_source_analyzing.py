"""Defines deterministic analysis for one supported source language."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_analysis import SourceAnalysis


"""
solid-name: LanguageSourceAnalyzing
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for producing typed deterministic analysis from normalized source content.
"""
class LanguageSourceAnalyzing(Protocol):
    def analyze(self, source: ResolvedAnalysisSource) -> SourceAnalysis: ...

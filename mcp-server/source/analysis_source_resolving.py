"""Defines normalization of file-backed and text-backed analysis sources."""

from typing import Protocol

from source.analyze_source_input import AnalyzeSourceInput
from source.resolved_analysis_source import ResolvedAnalysisSource


"""
solid-name: AnalysisSourceResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving one typed analysis source into normalized identity and content.
"""
class AnalysisSourceResolving(Protocol):
    def resolve(self, analysis_input: AnalyzeSourceInput) -> ResolvedAnalysisSource: ...

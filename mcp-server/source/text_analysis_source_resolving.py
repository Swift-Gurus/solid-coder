"""Defines text-backed source resolution."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: TextAnalysisSourceResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving in-memory text-backed analysis content.
"""
class TextAnalysisSourceResolving(Protocol):
    def resolve(self, source: TextAnalysisSource) -> ResolvedAnalysisSource: ...

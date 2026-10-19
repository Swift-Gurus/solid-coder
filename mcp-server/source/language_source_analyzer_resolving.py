"""Defines source-analyzer lookup by normalized language."""

from typing import Optional, Protocol, TypeVar

AnalysisCapability = TypeVar("AnalysisCapability", covariant=True)


"""
solid-name: LanguageSourceAnalyzerResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving a deterministic analyzer for a normalized source language.
"""
class LanguageSourceAnalyzerResolving(Protocol[AnalysisCapability]):
    def resolve(self, language: str) -> Optional[AnalysisCapability]: ...

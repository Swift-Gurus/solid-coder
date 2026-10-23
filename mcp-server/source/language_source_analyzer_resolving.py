"""Defines source-analyzer lookup by normalized language."""

from typing import Protocol, TypeVar

AnalysisCapability_co = TypeVar("AnalysisCapability_co", covariant=True)


"""
solid-name: LanguageSourceAnalyzerResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving a deterministic analyzer for a normalized source language.
"""


class LanguageSourceAnalyzerResolving(Protocol[AnalysisCapability_co]):
    def resolve(self, language: str) -> AnalysisCapability_co | None: ...

"""Defines source-analyzer lookup by normalized language."""

from typing import Optional, Protocol

from source.language_source_analyzing import LanguageSourceAnalyzing


"""
solid-name: LanguageSourceAnalyzerResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving a deterministic analyzer for a normalized source language.
"""
class LanguageSourceAnalyzerResolving(Protocol):
    def resolve(self, language: str) -> Optional[LanguageSourceAnalyzing]: ...

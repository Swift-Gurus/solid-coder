"""Defines deterministic source-language detection."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource


"""
solid-name: SourceLanguageDetecting
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for determining a normalized source language from resolved source identity and hints.
"""
class SourceLanguageDetecting(Protocol):
    def detect(self, source: ResolvedAnalysisSource) -> str: ...

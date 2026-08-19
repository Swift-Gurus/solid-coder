"""Associates a normalized language with its source analyzer."""

from dataclasses import dataclass

from source.language_source_analyzing import LanguageSourceAnalyzing


"""
solid-name: LanguageSourceAnalyzerRegistration
solid-category: model
solid-spec: [SPEC-040]
solid-description: Associates one normalized source language with its deterministic analysis capability.
"""
@dataclass(frozen=True)
class LanguageSourceAnalyzerRegistration:
    language: str
    analyzer: LanguageSourceAnalyzing

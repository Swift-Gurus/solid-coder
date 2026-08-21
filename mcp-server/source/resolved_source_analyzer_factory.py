"""Composes deterministic analysis for resolved source content."""

from gate.dict_extension_lookup import DictExtensionLookup
from source.language_source_analyzer_registration import (
    LanguageSourceAnalyzerRegistration,
)
from source.language_source_analyzer_resolver import (
    LanguageSourceAnalyzerResolver,
)
from source.resolved_source_analyzer import ResolvedSourceAnalyzer
from source.source_language_detector import SourceLanguageDetector
from source.swift_source_analyzer_factory import SwiftSourceAnalyzerFactory
from source.whole_document_unit_resolver import WholeDocumentUnitResolver


"""
solid-name: ResolvedSourceAnalyzerFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides language-selected parsed analysis with deterministic whole-document fallback for immutable source.
"""
class ResolvedSourceAnalyzerFactory:
    def make(self) -> ResolvedSourceAnalyzer:
        return ResolvedSourceAnalyzer(
            language_detector=SourceLanguageDetector(
                extension_lookup=DictExtensionLookup({
                    ".swift": "swift",
                    ".py": "python",
                }),
            ),
            analyzer_resolver=LanguageSourceAnalyzerResolver([
                LanguageSourceAnalyzerRegistration(
                    language="swift",
                    analyzer=SwiftSourceAnalyzerFactory().make(),
                )
            ]),
            document_unit_resolver=WholeDocumentUnitResolver(),
        )

"""Detects normalized source languages from hints and file identity."""

from gate.extension_lookup import ExtensionLookup
from gate.file_extension_extracting import FileExtensionExtracting
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_language_detecting import SourceLanguageDetecting


"""
solid-name: SourceLanguageDetector
solid-category: service
solid-spec: [SPEC-040]
solid-description: Detects a normalized source language from explicit hints or injected extension capabilities.
"""
class SourceLanguageDetector(SourceLanguageDetecting):
    def __init__(
        self,
        extension_extractor: FileExtensionExtracting,
        extension_lookup: ExtensionLookup,
    ) -> None:
        self._extension_extractor = extension_extractor
        self._extension_lookup = extension_lookup

    def detect(self, source: ResolvedAnalysisSource) -> str:
        if source.language_hint:
            return source.language_hint.strip().lower()
        extension = self._extension_extractor.suffix_of(source.identity)
        language = self._extension_lookup.language_for(extension)
        return language.lower() if language else extension.removeprefix(".") or "unknown"

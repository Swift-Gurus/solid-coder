"""Selects an internal parser language from exact file extension."""

from gate.extension_lookup import ExtensionLookup
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_language_detecting import SourceLanguageDetecting


"""
solid-name: SourceLanguageDetector
solid-category: service
solid-spec: [SPEC-040]
solid-description: Selects a normalized internal parser language from an exact file extension.
"""
class SourceLanguageDetector(SourceLanguageDetecting):
    def __init__(
        self,
        extension_lookup: ExtensionLookup,
    ) -> None:
        self._extension_lookup = extension_lookup

    def detect(self, source: ResolvedAnalysisSource) -> str:
        language = self._extension_lookup.language_for(source.file_extension)
        return language.lower() if language else "unsupported"

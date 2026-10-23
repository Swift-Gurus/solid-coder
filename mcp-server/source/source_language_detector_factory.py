"""Composes the shared source-language selection policy."""

from gate.dict_extension_lookup import DictExtensionLookup
from source.source_language_detector import SourceLanguageDetector

"""
solid-name: SourceLanguageDetectorFactory
solid-category: factory
solid-spec: [SPEC-040, SPEC-064]
solid-description: Creates the shared source-language detector.
"""


class SourceLanguageDetectorFactory:
    def make(self) -> SourceLanguageDetector:
        return SourceLanguageDetector(
            DictExtensionLookup(
                {
                    ".swift": "swift",
                    ".py": "python",
                }
            )
        )

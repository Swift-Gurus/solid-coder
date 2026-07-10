"""
solid-description: Resolves file extensions to their corresponding language names.
solid-category: service
solid-tags: [hook]
"""

from typing import Optional


class DictExtensionLookup:
    """Boundary adapter: wraps a plain {ext: language} dict for ExtensionLookup conformance."""

    def __init__(self, mapping: dict) -> None:
        self._mapping = mapping

    def language_for(self, ext: str) -> Optional[str]:
        return self._mapping.get(ext)

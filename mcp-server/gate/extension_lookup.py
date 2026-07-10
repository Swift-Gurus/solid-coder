"""
solid-description: Contract for resolving a file extension to its supported language name.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Optional, Protocol


class ExtensionLookup(Protocol):
    def language_for(self, ext: str) -> Optional[str]: ...

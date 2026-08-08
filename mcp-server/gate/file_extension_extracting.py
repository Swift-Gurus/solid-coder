"""Defines normalized file-extension extraction."""

from typing import Protocol


"""
solid-name: FileExtensionExtracting
solid-category: abstraction
solid-description: Contract for obtaining a normalized extension from a file path.
solid-tags: [hook]
"""
class FileExtensionExtracting(Protocol):
    def suffix_of(self, file_path: str) -> str: ...

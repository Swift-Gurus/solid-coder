"""
solid-description: Contract for extracting suffixes from file paths.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class PathExtracting(Protocol):
    """Extracts the lowercased file extension from a path string."""

    def suffix_of(self, file_path: str) -> str: ...

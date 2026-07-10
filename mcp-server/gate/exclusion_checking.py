"""
solid-description: Contract for checking whether a file path is excluded from gate checks.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class ExclusionChecking(Protocol):
    def is_excluded(self, file_path: str) -> bool: ...

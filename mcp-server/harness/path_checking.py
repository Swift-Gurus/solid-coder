"""
solid-description: Checks whether a file path exists on disk.
solid-category: service
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class PathChecking(Protocol):
    """
    solid-description: Contract for checking whether a file path exists on disk.
    solid-category: abstraction
    """

    def exists(self, path: str) -> bool: ...


class PathChecker:
    """
    solid-description: Checks whether a file path exists on disk.
    solid-category: service
    """

    def exists(self, path: str) -> bool:
        return Path(path).exists()

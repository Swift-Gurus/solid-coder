"""
solid-description: Creates directories and all required parent directories.
solid-category: utility
solid-tags: [hook, llm]
"""

from pathlib import Path
from typing import Protocol


class DirectoryCreating(Protocol):
    def create(self, path: Path) -> None: ...


class PathDirectoryCreator:
    """Boundary adapter: creates directories via Path.mkdir."""

    def create(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

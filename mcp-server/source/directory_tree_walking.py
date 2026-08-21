"""Defines recursive file traversal at the filesystem boundary."""

from pathlib import Path
from typing import Protocol


"""
solid-name: DirectoryTreeWalking
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for recursively listing files while applying caller-owned directory exclusions.
"""
class DirectoryTreeWalking(Protocol):
    def files(
        self,
        root: Path,
        excluded_directories: frozenset[str],
    ) -> list[Path]: ...

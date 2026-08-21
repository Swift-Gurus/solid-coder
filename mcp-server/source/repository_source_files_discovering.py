"""Defines project source-file discovery for repository analysis."""

from pathlib import Path
from typing import Protocol


"""
solid-name: RepositorySourceFilesDiscovering
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for discovering ordered source-file paths beneath one project root.
"""
class RepositorySourceFilesDiscovering(Protocol):
    def discover(self, project_root: Path) -> list[Path]: ...

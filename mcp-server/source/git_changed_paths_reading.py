"""Defines categorized Git path discovery."""

from pathlib import Path
from typing import Protocol

from source.git_changed_paths import GitChangedPaths


"""
solid-name: GitChangedPathsReading
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for reading categorized changed paths from a Git working tree.
"""
class GitChangedPathsReading(Protocol):
    def read(self, project_root: Path) -> GitChangedPaths: ...

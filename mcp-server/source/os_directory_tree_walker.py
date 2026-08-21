"""Adapts recursive operating-system traversal to a typed file list."""

import os
from pathlib import Path

from source.directory_tree_walking import DirectoryTreeWalking


"""
solid-name: OsDirectoryTreeWalker
solid-category: adapter
solid-spec: [SPEC-040]
solid-description: Lists files recursively while honoring a supplied set of excluded directory names.
"""
class OsDirectoryTreeWalker(DirectoryTreeWalking):
    """Boundary adapter around the standard-library directory walk API."""

    def files(
        self,
        root: Path,
        excluded_directories: frozenset[str],
    ) -> list[Path]:
        discovered: list[Path] = []
        for directory, directories, filenames in os.walk(root):
            directories[:] = [
                name
                for name in directories
                if name not in excluded_directories
            ]
            discovered.extend(
                Path(directory) / filename
                for filename in filenames
            )
        return discovered

"""
solid-description: Produces the directory chain from a root directory down to a file's parent in root-to-leaf order.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Protocol

from scoring.parent_chain import ParentChaining


class DirectoryWalking(Protocol):
    def directories(self, file_path: str, root: Path) -> list: ...


class DirectoryWalker:
    """Produces the directory chain from root to file directory (root→leaf order)."""

    def __init__(self, chainer: ParentChaining) -> None:
        self._chain = chainer

    def directories(self, file_path: str, root: Path) -> list:
        dirs = []
        for current in self._chain(Path(file_path).resolve().parent):
            dirs.append(current)
            if current == root:
                break
        return list(reversed(dirs))  # root → leaf

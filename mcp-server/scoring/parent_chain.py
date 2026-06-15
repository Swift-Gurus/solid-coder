"""
solid-description: Enumerates parent directories from a starting path to the filesystem root.
solid-category: utility
solid-tags: [utility]
"""

from pathlib import Path
from typing import Iterator, Protocol


class ParentChaining(Protocol):
    def __call__(self, start: Path) -> Iterator[Path]: ...


def parent_chain(start: Path) -> Iterator[Path]:
    """Yields each directory from start up to the filesystem root (inclusive)."""
    current = start
    while True:
        yield current
        if current.parent == current:
            break
        current = current.parent

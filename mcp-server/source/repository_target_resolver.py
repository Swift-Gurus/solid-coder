"""Resolves project source targets within the selected Git repository."""

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

"""
solid-name: RepositoryTargetResolving
solid-category: abstraction
solid-spec: [SPEC-071]
solid-description: Contract for resolving project review and search targets within their selected repository boundary.
"""


class RepositoryTargetResolving(Protocol):
    def resolve(self, cwd: Path, target: Path) -> Path: ...


"""
solid-name: RepositoryTargetResolver
solid-category: utility
solid-spec: [SPEC-071]
solid-description: Canonicalizes project source targets against the nearest Git root and rejects traversal and symlink escapes before source content is read.
"""


class RepositoryTargetResolver(RepositoryTargetResolving):
    def __init__(self, root_finder: Callable[[Path], Path | None]) -> None:
        self._root_finder = root_finder

    def resolve(self, cwd: Path, target: Path) -> Path:
        root = self._root_finder(cwd)
        if root is None:
            raise ValueError(
                f"No Git repository found for '{cwd}'; cannot resolve target '{target}'"
            )
        root = root.resolve()
        resolved = (root / target).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(
                f"Source target '{target}' resolves outside repository '{root}': '{resolved}'"
            )
        return resolved

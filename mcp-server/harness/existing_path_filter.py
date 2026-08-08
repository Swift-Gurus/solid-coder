"""Filters workflow search paths through the filesystem boundary."""

from __future__ import annotations

from pathlib import Path

from harness.path_checking import PathChecking
from harness.path_filtering import PathFiltering


"""
solid-name: ExistingPathFilter
solid-category: service
solid-spec: [SPEC-031]
solid-description: Retains existing workflow search directories in their declared precedence order.
"""
class ExistingPathFilter(PathFiltering):

    def __init__(self, path_checker: PathChecking) -> None:
        self._path_checker = path_checker

    def filter(self, paths: list[Path]) -> list[Path]:
        return [path for path in paths if self._path_checker.exists(str(path))]

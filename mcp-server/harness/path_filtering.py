"""Defines filtering of ordered workflow search paths."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


"""
solid-name: PathFiltering
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for filtering an ordered workflow search-path collection by filesystem eligibility.
"""
class PathFiltering(Protocol):

    def filter(self, paths: list[Path]) -> list[Path]: ...

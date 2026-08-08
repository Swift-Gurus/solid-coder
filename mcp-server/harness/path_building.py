"""Defines construction of normalized filesystem paths."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


"""
solid-name: PathBuilding
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for constructing a normalized path from a base value and optional child reference.
"""
class PathBuilding(Protocol):
    def build(self, base: str | Path, child: str | None = None) -> Path: ...

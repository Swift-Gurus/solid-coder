"""Constructs normalized filesystem paths."""

from __future__ import annotations

from pathlib import Path


"""
solid-name: PathBuilder
solid-category: service
solid-spec: [SPEC-035]
solid-description: Constructs a normalized path from a base value and optional child reference.
"""
class PathBuilder:
    def build(self, base: str | Path, child: str | None = None) -> Path:
        path = Path(base)
        return (path / child).resolve() if child is not None else path.resolve()

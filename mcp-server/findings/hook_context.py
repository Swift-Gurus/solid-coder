"""Represents authoritative context for one health-check submission."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


"""
solid-name: HookContext
solid-category: model
solid-description: Provides immutable authoritative file and unit context for one health-check output directory.
"""
@dataclass(frozen=True)
class HookContext:
    output_directory: Path
    file_path: str
    language: str
    expected_units: tuple[str, ...]

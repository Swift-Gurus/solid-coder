"""Defines the location and ownership of one discoverable workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


"""
solid-name: WorkflowSource
solid-category: model
solid-spec: [SPEC-035]
solid-description: Identifies one discoverable workflow and the package that owns its entrypoint.
"""
@dataclass(frozen=True)
class WorkflowSource:
    id: str
    entry_path: Path
    package_root: Path | None
    legacy: bool = False

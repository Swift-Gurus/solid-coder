"""Defines workflow package ownership lookup."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


"""
solid-name: WorkflowPackageRootLocating
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for locating the workflow package root owning a resource file.
"""
class WorkflowPackageRootLocating(Protocol):
    def locate(self, declaring_file: Path) -> Path | None: ...

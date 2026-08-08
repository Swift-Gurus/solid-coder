"""Defines package entrypoint validation."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


"""
solid-name: WorkflowPackageValidating
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for validating required workflow package entrypoint fields.
"""
class WorkflowPackageValidating(Protocol):
    def validate(self, path: Path, raw: dict | None) -> None: ...

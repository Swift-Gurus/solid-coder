"""Defines loading of a required output schema resource."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


"""
solid-name: OutputSchemaFileLoading
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for loading a required output schema relative to its declaring workflow file.
"""
class OutputSchemaFileLoading(Protocol):
    def load(self, declaring_file: Path, reference: str, step_id: str, output_name: str) -> dict: ...

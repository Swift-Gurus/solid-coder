"""Defines one declared workflow step output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


"""
solid-name: OutputSpec
solid-category: model
solid-spec: [SPEC-030]
solid-description: Represents the name, type, and validation schema of one step output.
"""
@dataclass(frozen=True)
class OutputSpec:
    name: str
    type: str
    schema: Optional[dict] = None
    schema_file: Optional[str] = None

"""Defines one declared workflow step output."""

from __future__ import annotations

from dataclasses import dataclass


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
    schema: dict | None = None
    schema_file: str | None = None

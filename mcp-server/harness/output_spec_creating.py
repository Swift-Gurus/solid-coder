"""Defines output-specification creation."""

from __future__ import annotations

from typing import Protocol

from harness.output_spec import OutputSpec


"""
solid-name: OutputSpecCreating
solid-category: abstraction
solid-spec: [SPEC-030]
solid-description: Contract for creating a workflow-step output specification.
"""
class OutputSpecCreating(Protocol):
    def create(
        self,
        name: str,
        output_type: str,
        schema: dict | None,
        schema_file: str | None,
    ) -> OutputSpec: ...

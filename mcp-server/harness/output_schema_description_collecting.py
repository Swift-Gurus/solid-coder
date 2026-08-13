"""Defines output-schema requirement collection."""

from __future__ import annotations

from typing import Protocol

from harness.output_spec import OutputSpec


"""
solid-name: OutputSchemaDescriptionCollecting
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for describing the schema requirements declared by workflow-step outputs.
"""
class OutputSchemaDescriptionCollecting(Protocol):
    def collect(self, outputs: list[OutputSpec]) -> list[str]: ...

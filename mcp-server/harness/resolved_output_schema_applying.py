"""Defines application of a loaded schema to an output specification."""

from typing import Protocol

from harness.output_spec import OutputSpec


"""
solid-name: ResolvedOutputSchemaApplying
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for applying a loaded JSON schema to an output specification.
"""
class ResolvedOutputSchemaApplying(Protocol):

    def apply(self, output: OutputSpec, schema: dict) -> OutputSpec: ...

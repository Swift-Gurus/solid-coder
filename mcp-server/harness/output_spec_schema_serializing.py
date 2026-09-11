"""Declares model-output schema serialization."""

from typing import Protocol

from harness.output_spec import OutputSpec


"""
solid-name: OutputSpecSchemaSerializing
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for serializing one resolved output specification into its JSON Schema representation.
"""
class OutputSpecSchemaSerializing(Protocol):
    def serialize(self, output: OutputSpec) -> dict[str, object]: ...

"""Defines the authored-step fields used by aggregate presentation."""

from typing import Protocol

from harness.output_spec import OutputSpec


"""
solid-name: AuthoredStepReading
solid-category: abstraction
solid-spec: [SPEC-052]
solid-description: Contract for reading authored step identity, instructions, and outputs.
"""
class AuthoredStepReading(Protocol):
    workflow_id: str
    step_id: str
    prompt: str
    outputs: list[OutputSpec]

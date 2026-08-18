"""Defines one named output value submitted for schema validation."""

from dataclasses import dataclass

from harness.output_spec import OutputSpec


"""
solid-name: StepOutputSubmission
solid-category: model
solid-spec: [SPEC-031, SPEC-039]
solid-description: Represents one workflow instance output specification and its submitted value.
"""
@dataclass(frozen=True)
class StepOutputSubmission:
    instance_id: str
    specification: OutputSpec
    value: object

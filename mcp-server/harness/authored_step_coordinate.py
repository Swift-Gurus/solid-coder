"""Identifies one authored model step and its output contract."""

from dataclasses import dataclass, field

from harness.output_spec import OutputSpec


"""
solid-name: AuthoredStepCoordinate
solid-category: model
solid-spec: [SPEC-045]
solid-description: Carries stable authored workflow-step identity, instructions, and declared outputs.
"""
@dataclass(frozen=True)
class AuthoredStepCoordinate:
    workflow_id: str
    step_id: str
    prompt: str
    outputs: list[OutputSpec] = field(default_factory=list)

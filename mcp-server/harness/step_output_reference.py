"""Defines a typed reference to one workflow step output."""

from dataclasses import dataclass


"""
solid-name: StepOutputReference
solid-category: model
solid-spec: [SPEC-030, SPEC-037]
solid-description: Identifies one local workflow step and one declared output selected by an authored expression.
"""
@dataclass(frozen=True)
class StepOutputReference:
    step_id: str
    output_name: str

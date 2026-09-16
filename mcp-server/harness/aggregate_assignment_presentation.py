"""Defines the presentation fields used to collect aggregate assignments."""

from typing import Protocol

from harness.authored_step_reading import AuthoredStepReading


"""
solid-name: AggregateAssignmentPresentation
solid-category: abstraction
solid-spec: [SPEC-052]
solid-description: Contract for reading the model-facing address and authored step of an aggregate assignment.
"""
class AggregateAssignmentPresentation(Protocol):
    label: str
    workflow_alias: str
    authored_step: AuthoredStepReading

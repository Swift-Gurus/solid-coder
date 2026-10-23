"""Defines the presentation fields used to collect aggregate assignments."""

from typing import Protocol

from harness.authored_step_reading import AuthoredStepReading

"""
solid-name: AggregateAssignmentPresentation
solid-category: abstraction
solid-spec: [SPEC-052]
solid-description: Contract for presenting the identifying context and source work of an aggregate assignment.
"""


class AggregateAssignmentPresentation(Protocol):
    label: str
    workflow_alias: str
    authored_step: AuthoredStepReading

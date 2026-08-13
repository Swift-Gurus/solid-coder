"""Defines validation of workflow-step identity uniqueness."""

from typing import Protocol

from harness.graph_step_field_reading import GraphStepFieldReading


"""
solid-name: UniqueStepIdentityValidating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for rejecting duplicate workflow-step identifiers.
"""
class UniqueStepIdentityValidating(Protocol):

    def validate(self, steps: list[GraphStepFieldReading]) -> None: ...

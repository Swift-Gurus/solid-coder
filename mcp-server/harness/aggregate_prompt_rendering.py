"""Declares aggregate assignment prompt rendering."""

from typing import Protocol

from harness.aggregate_assignment import AggregateAssignment


"""
solid-name: AggregatePromptRendering
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for rendering compact model instructions and an applicability matrix from typed assignments.
"""
class AggregatePromptRendering(Protocol):
    def render(self, assignments: list[AggregateAssignment]) -> str: ...

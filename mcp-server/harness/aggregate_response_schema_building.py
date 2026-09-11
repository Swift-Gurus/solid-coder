"""Declares aggregate response-schema construction."""

from typing import Protocol

from harness.aggregate_assignment import AggregateAssignment


"""
solid-name: AggregateResponseSchemaBuilding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for building an exact model-submission schema from typed aggregate assignments.
"""
class AggregateResponseSchemaBuilding(Protocol):
    def build(self, assignments: list[AggregateAssignment]) -> dict[str, object]: ...

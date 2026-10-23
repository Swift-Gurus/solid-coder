"""Declares aggregate response-schema construction."""

from typing import Protocol

from harness.aggregate_assignment import AggregateAssignment

"""
solid-name: AggregateResponseSchemaBuilding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for constructing response schemas for aggregate submissions.
"""


class AggregateResponseSchemaBuilding(Protocol):
    def build(self, assignments: list[AggregateAssignment]) -> dict[str, object]: ...

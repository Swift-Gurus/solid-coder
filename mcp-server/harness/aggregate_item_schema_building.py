"""Declares aggregate item-schema construction."""

from typing import Protocol

from harness.aggregate_assignment import AggregateAssignment
from harness.strict_object_schema import StrictObjectSchema


"""
solid-name: AggregateItemSchemaBuilding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for building the strict workflow-addressed schema of one aggregate item.
"""
class AggregateItemSchemaBuilding(Protocol):
    def build(
        self,
        item_label: str,
        assignments: list[AggregateAssignment],
    ) -> StrictObjectSchema: ...

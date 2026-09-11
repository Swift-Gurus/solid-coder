"""Declares aggregate workflow-schema construction."""

from typing import Protocol

from harness.aggregate_assignment import AggregateAssignment
from harness.strict_object_schema import StrictObjectSchema


"""
solid-name: AggregateWorkflowSchemaBuilding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for building the strict step-addressed schema of one aggregate workflow assignment.
"""
class AggregateWorkflowSchemaBuilding(Protocol):
    def build(self, assignment: AggregateAssignment) -> StrictObjectSchema: ...

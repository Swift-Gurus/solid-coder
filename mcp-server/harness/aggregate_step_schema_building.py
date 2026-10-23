"""Declares aggregate step-schema construction."""

from typing import Protocol

from harness.authored_step_coordinate import AuthoredStepCoordinate
from harness.strict_object_schema import StrictObjectSchema

"""
solid-name: AggregateStepSchemaBuilding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for deriving an aggregate step's output schema.
"""


class AggregateStepSchemaBuilding(Protocol):
    def build(self, step: AuthoredStepCoordinate) -> StrictObjectSchema: ...

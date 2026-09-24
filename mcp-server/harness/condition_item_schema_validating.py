"""Defines static validation of item references in workflow conditions."""

from typing import Protocol

from harness.condition_declaration import ConditionDeclaration
from harness.workflow_data_schema import WorkflowDataSchema


"""
solid-name: ConditionItemSchemaValidating
solid-category: abstraction
solid-spec: [SPEC-053]
solid-description: Contract for validating condition item references against an authored schema.
"""
class ConditionItemSchemaValidating(Protocol):
    def validate(
        self,
        step_id: str,
        condition: ConditionDeclaration,
        item_schema: WorkflowDataSchema,
    ) -> None: ...

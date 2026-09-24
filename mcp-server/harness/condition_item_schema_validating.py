"""Defines static validation of item references in workflow conditions."""

from typing import Optional, Protocol

from harness.condition_declaration import ConditionDeclaration
from harness.workflow_data_schema import WorkflowDataSchema
from harness.workflow_expression import WorkflowExpression


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
        reference_name: str = "scoring.when",
    ) -> None: ...

    def validate_reference(
        self,
        step_id: str,
        reference_name: str,
        reference: WorkflowExpression,
        item_schema: WorkflowDataSchema,
        allowed_types: Optional[list[str]] = None,
    ) -> None: ...

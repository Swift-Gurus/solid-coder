"""Validates condition item references against an authored item schema."""

from harness.condition_declaration import ConditionDeclaration
from harness.condition_item_schema_validating import ConditionItemSchemaValidating
from harness.condition_reference_collecting import ConditionReferenceCollecting
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.workflow_data_schema import WorkflowDataSchema
from harness.workflow_expression import WorkflowExpression

"""
solid-name: ConditionItemSchemaValidator
solid-category: service
solid-spec: [SPEC-053]
solid-description: Validates statically addressable condition item fields.
"""


class ConditionItemSchemaValidator(ConditionItemSchemaValidating):
    def __init__(
        self,
        reference_collector: ConditionReferenceCollecting,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._reference_collector = reference_collector
        self._error_factory = error_factory

    def validate(
        self,
        step_id: str,
        condition: ConditionDeclaration,
        item_schema: WorkflowDataSchema,
        reference_name: str = "scoring.when",
    ) -> None:
        for reference in self._reference_collector.collect(condition):
            self.validate_reference(
                step_id,
                reference_name,
                reference,
                item_schema,
            )

    def validate_reference(
        self,
        step_id: str,
        reference_name: str,
        reference: WorkflowExpression,
        item_schema: WorkflowDataSchema,
        allowed_types: list[str] | None = None,
        root: str = "item",
        allowed_item_types: list[str] | None = None,
    ) -> None:
        components = reference.value.split(".")
        if not components or components[0] != root:
            return
        current_schema = item_schema
        for field_name in components[1:]:
            property_schema = current_schema.property(field_name)
            if property_schema is None:
                raise self._error_factory.create(
                    f"Metric step '{step_id}' {reference_name} item field "
                    f"'{field_name}' is not declared by the source item schema"
                )
            current_schema = property_schema
        if allowed_types is not None and current_schema.type not in allowed_types:
            raise self._error_factory.create(
                f"Metric step '{step_id}' {reference_name} must reference an "
                f"item field with schema type {' or '.join(allowed_types)}"
            )
        if allowed_item_types is not None and (
            current_schema.items is None
            or current_schema.items.type not in allowed_item_types
        ):
            raise self._error_factory.create(
                f"Metric step '{step_id}' {reference_name} must reference an "
                "array with a declared scalar item schema"
            )

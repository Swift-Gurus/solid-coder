"""Validates condition item references against an authored item schema."""

from harness.condition_declaration import ConditionDeclaration
from harness.condition_item_schema_validating import ConditionItemSchemaValidating
from harness.condition_reference_collecting import ConditionReferenceCollecting
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.workflow_data_schema import WorkflowDataSchema


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
    ) -> None:
        for reference in self._reference_collector.collect(condition):
            components = reference.value.split(".")
            if not components or components[0] != "item":
                continue
            current_schema = item_schema
            for field_name in components[1:]:
                property_schema = current_schema.property(field_name)
                if property_schema is None:
                    raise self._error_factory.create(
                        f"Metric step '{step_id}' scoring.when item field "
                        f"'{field_name}' is not declared by the source item schema"
                    )
                current_schema = property_schema

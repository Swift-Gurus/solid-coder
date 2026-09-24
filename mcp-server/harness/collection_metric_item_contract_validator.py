"""Validates collection metric behavior against its resolved item schema."""

from typing import Optional

from harness.collection_metric_item_contract_validating import (
    CollectionMetricItemContractValidating,
)
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.condition_declaration import ConditionDeclaration
from harness.condition_item_schema_validating import ConditionItemSchemaValidating
from harness.workflow_data_schema import WorkflowDataSchema


"""
solid-name: CollectionMetricItemContractValidator
solid-category: service
solid-spec: [SPEC-053, SPEC-054, SPEC-056]
solid-description: Applies shared filter and reducer field validation to any typed collection source item.
"""
class CollectionMetricItemContractValidator(
    CollectionMetricItemContractValidating
):
    def __init__(
        self,
        item_schema_validator: ConditionItemSchemaValidating,
    ) -> None:
        self._item_schema_validator = item_schema_validator

    def validate(
        self,
        target_id: str,
        item_schema: WorkflowDataSchema,
        condition: Optional[ConditionDeclaration],
        reducer: Optional[CollectionMetricReducer],
    ) -> None:
        if condition is not None:
            self._item_schema_validator.validate(
                target_id,
                condition,
                item_schema,
            )
        if reducer is None:
            return
        if reducer.value is not None:
            allowed_types = (
                ["integer", "number"]
                if reducer.type in {
                    CollectionMetricReducerType.MAXIMUM,
                    CollectionMetricReducerType.MINIMUM,
                }
                else ["integer", "number", "string", "boolean", "null"]
            )
            self._item_schema_validator.validate_reference(
                target_id,
                f"{reducer.type.value} reducer value",
                reducer.value,
                item_schema,
                allowed_types,
            )
        if reducer.numerator_condition is not None:
            self._item_schema_validator.validate(
                target_id,
                reducer.numerator_condition,
                item_schema,
                "reducer numerator_when",
            )
        if reducer.denominator_condition is not None:
            self._item_schema_validator.validate(
                target_id,
                reducer.denominator_condition,
                item_schema,
                "reducer denominator_when",
            )

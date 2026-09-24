"""Validates workflow for-each references."""

from __future__ import annotations

from harness.collection_metric_item_contract_validating import (
    CollectionMetricItemContractValidating,
)
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.for_each_target_validating import ForEachTargetValidating
from harness.for_each_validation_target import ForEachValidationTarget
from harness.models import StepDef
from harness.step_dependency_reachability_checking import (
    StepDependencyReachabilityChecking,
)
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_data_schema import WorkflowDataSchema


"""
solid-name: ForEachReferenceValidator
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Validates workflow iteration syntax, source outputs, array schemas, and dependency reachability.
"""
class ForEachReferenceValidator(ForEachTargetValidating):
    def __init__(
        self,
        reachability_checker: StepDependencyReachabilityChecking,
        item_contract_validator: CollectionMetricItemContractValidating,
        schema_decoder: StructuredModelDecoding[WorkflowDataSchema],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._reachability_checker = reachability_checker
        self._item_contract_validator = item_contract_validator
        self._schema_decoder = schema_decoder
        self._error_factory = error_factory

    def validate(
        self,
        target: ForEachValidationTarget,
        steps: list[StepDef],
    ) -> None:
        source_step = next(
            (
                candidate
                for candidate in steps
                if candidate.id == target.source_step_id
            ),
            None,
        )
        if source_step is None:
            raise self._error_factory.create(
                f"Step '{target.target_id}' {target.reference_name} references unknown step "
                f"'{target.source_reference.step_id}'"
            )
        source_output = next(
            (
                output
                for output in source_step.outputs
                if output.name == target.source_reference.output_name
            ),
            None,
        )
        if source_output is None:
            raise self._error_factory.create(
                f"Step '{target.target_id}' {target.reference_name} references unknown output "
                f"'{target.source_reference.output_name}' on step "
                f"'{target.source_reference.step_id}'"
            )
        if not self._reachability_checker.is_dependency(
            target.source_step_id,
            target.dependency_ids,
            steps,
        ):
            raise self._error_factory.create(
                f"Step '{target.target_id}' {target.reference_name} must reference a transitive dependency"
            )
        if source_output.schema is None:
            raise self._error_factory.create(
                f"Step '{target.target_id}' {target.reference_name} source output "
                f"'{target.source_reference.output_name}' must declare an array schema"
            )
        source_schema = self._schema_decoder.decode(
            source_output.schema,
            f"step '{target.source_reference.step_id}' output schema",
        )
        if source_schema.type != "array":
            raise self._error_factory.create(
                f"Step '{target.target_id}' {target.reference_name} source output "
                f"'{target.source_reference.output_name}' must declare an array schema"
            )
        item_schema = source_schema.items or WorkflowDataSchema()
        self._item_contract_validator.validate(
            target.target_id,
            item_schema,
            target.item_condition,
            target.metric_reducer,
        )

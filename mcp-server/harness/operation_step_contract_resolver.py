"""Decodes authored operation steps against registered typed contracts."""

from __future__ import annotations

from collections.abc import Mapping

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.operation_output_specs_resolving import OperationOutputSpecsResolving
from harness.operation_registration_resolving import (
    OperationRegistrationResolving,
)
from harness.operation_step import OperationStep
from harness.operation_step_contract import OperationStepContract
from harness.operation_step_contract_resolving import (
    OperationStepContractResolving,
)
from harness.workflow_expression_parsing import WorkflowExpressionParsing
from harness.workflow_input_binding import WorkflowInputBinding


"""
solid-name: OperationStepContractResolver
solid-category: boundary
solid-spec: [SPEC-010, SPEC-040]
solid-description: Decodes authored operation fields into typed logical steps and registered output contracts.
"""
class OperationStepContractResolver(OperationStepContractResolving):
    def __init__(
        self,
        registry: OperationRegistrationResolving,
        expression_parser: WorkflowExpressionParsing,
        output_specs_resolver: OperationOutputSpecsResolving,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._registry = registry
        self._expression_parser = expression_parser
        self._output_specs_resolver = output_specs_resolver
        self._error_factory = error_factory

    def resolve(self, raw: object) -> OperationStepContract:
        if not isinstance(raw, Mapping) or raw.get("type") != "operation":
            return OperationStepContract()
        name = raw.get("operation")
        if not isinstance(name, str) or not name:
            raise self._error_factory.create(
                f"Step '{raw.get('id')}' is type 'operation' and must declare an operation"
            )
        registration = self._registry.resolve(name)
        raw_bindings = raw.get("with") or {}
        if not isinstance(raw_bindings, Mapping):
            raise self._error_factory.create(
                f"Operation step '{raw.get('id')}' must declare 'with' as an object"
            )
        input_fields = registration.input_model.model_fields
        unknown = [key for key in raw_bindings if key not in input_fields]
        missing = [
            key
            for key, field in input_fields.items()
            if field.is_required() and key not in raw_bindings
        ]
        if unknown:
            raise self._error_factory.create(
                f"Operation step '{raw.get('id')}' has unknown input '{unknown[0]}'"
            )
        if missing:
            raise self._error_factory.create(
                f"Operation step '{raw.get('id')}' is missing required input '{missing[0]}'"
            )
        return OperationStepContract(
            step=OperationStep(
                name=name,
                input_bindings=[
                    WorkflowInputBinding(
                        name=key,
                        expression=self._expression_parser.parse(value),
                    )
                    for key, value in raw_bindings.items()
                ],
            ),
            outputs=self._output_specs_resolver.resolve(
                registration.output_model
            ),
        )

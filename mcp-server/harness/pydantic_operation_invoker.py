"""Invokes registered operations across the dynamic Pydantic boundary."""

from pydantic import BaseModel, ValidationError

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.operation_invoking import OperationInvoking
from harness.operation_registration import OperationRegistration
from harness.workflow_context_values import WorkflowContextValues


"""
solid-name: PydanticOperationInvoker
solid-category: boundary
solid-spec: [SPEC-010, SPEC-040]
solid-description: Validates dynamic operation inputs and outputs while invoking the registered typed handler.
"""
class PydanticOperationInvoker(OperationInvoking):
    def __init__(
        self,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._error_factory = error_factory

    def invoke(
        self,
        registration: OperationRegistration,
        inputs: WorkflowContextValues[object],
    ) -> BaseModel:
        try:
            operation_input = registration.input_model.model_validate(
                {entry.name: entry.value for entry in inputs.entries}
            )
            output = registration.handler.execute(operation_input)
            return registration.output_model.model_validate(output)
        except ValidationError as error:
            raise self._error_factory.create(
                f"Invalid '{registration.name}' operation data: {error}"
            ) from error

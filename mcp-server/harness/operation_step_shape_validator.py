"""Validates internal logical-operation workflow steps."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.step_declaration import StepDeclaration
from harness.step_field_validating import StepFieldValidating


"""
solid-name: OperationStepShapeValidator
solid-category: service
solid-spec: [SPEC-010, SPEC-040]
solid-description: Validates fields permitted on internal logical-operation steps.
"""
class OperationStepShapeValidator(StepFieldValidating[StepDeclaration]):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, step: StepDeclaration) -> None:
        if step.operation is None:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'operation' and must declare an operation"
            )
        if step.prompt or step.prompt_file:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'operation' and must not declare a prompt"
            )
        if step.command is not None or step.script_file is not None:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'operation' and must not declare a process command"
            )
        if step.mode is not None:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'operation' and must not declare a mode"
            )

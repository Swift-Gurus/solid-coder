"""Validates model-owned and engine-owned metric step shapes."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.step_declaration import StepDeclaration
from harness.step_field_validating import StepFieldValidating


"""
solid-name: MetricStepShapeValidator
solid-category: service
solid-spec: [SPEC-053]
solid-description: Validates execution ownership declared by metric workflow steps.
"""
class MetricStepShapeValidator(StepFieldValidating[StepDeclaration]):
    def __init__(
        self,
        model_owned_validator: StepFieldValidating[StepDeclaration],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._model_owned_validator = model_owned_validator
        self._error_factory = error_factory

    def validate(self, step: StepDeclaration) -> None:
        if step.metric_calculation is None:
            self._model_owned_validator.validate(step)
            return
        if step.prompt or step.prompt_file:
            raise self._error_factory.create(
                f"Step '{step.id}' collection-backed metric must not declare a prompt"
            )
        if step.command is not None or step.script_file is not None:
            raise self._error_factory.create(
                f"Step '{step.id}' collection-backed metric must not declare a process command"
            )
        if step.operation is not None or step.mode is not None:
            raise self._error_factory.create(
                f"Step '{step.id}' collection-backed metric must not declare an execution mode"
            )
        if step.for_each is not None:
            raise self._error_factory.create(
                f"Step '{step.id}' collection-backed metric must not declare for_each"
            )

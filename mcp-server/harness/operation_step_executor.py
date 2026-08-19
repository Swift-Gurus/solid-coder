"""Executes one engine-owned logical operation step."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.models import StepDef
from harness.operation_input_supplying import OperationInputSupplying
from harness.operation_invoking import OperationInvoking
from harness.operation_registration_resolving import OperationRegistrationResolving
from harness.operation_step_running import OperationStepRunning
from harness.step_run_outcome import StepRunOutcome


"""
solid-name: OperationStepExecutor
solid-category: service
solid-spec: [SPEC-010, SPEC-040]
solid-description: Executes an engine-owned logical operation and exposes its validated structured outputs.
"""
class OperationStepExecutor(OperationStepRunning):
    def __init__(
        self,
        registry: OperationRegistrationResolving,
        invoker: OperationInvoking,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._registry = registry
        self._invoker = invoker
        self._error_factory = error_factory

    def run(
        self,
        step_instance: OperationInputSupplying,
        step_def: StepDef,
    ) -> StepRunOutcome:
        if step_def.operation is None:
            raise self._error_factory.create(
                f"Operation step '{step_def.id}' has no operation declaration"
            )
        output = self._invoker.invoke(
            self._registry.resolve(step_def.operation.name),
            step_instance.inputs,
        )
        return StepRunOutcome(
            awaiting_input=False,
            outputs=output.model_dump(mode="json"),
        )

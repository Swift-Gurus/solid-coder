"""Resolves completed outputs required by deterministic rule finalization."""

from harness.completed_step_outputs_resolving import CompletedStepOutputsResolving
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.run_state import RunState
from harness.step_outputs import StepOutputs


"""
solid-name: CompletedStepOutputsResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Resolves required completed step outputs or reports missing runtime evidence.
"""
class CompletedStepOutputsResolver(CompletedStepOutputsResolving):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def resolve(
        self,
        step_id: str,
        run_state: RunState,
    ) -> StepOutputs:
        outputs = run_state.completed.get(step_id)
        if outputs is None:
            raise self._error_factory.create(
                f"Rule step '{step_id}' has no completed outputs"
            )
        return outputs

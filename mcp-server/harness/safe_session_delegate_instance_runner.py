"""Executes one delegated session and converts runner failures into outcomes."""

from __future__ import annotations

from harness.delegate_instruction_building import DelegateInstructionBuilding
from harness.models import StepInstance
from harness.session_delegate_instance_running import SessionDelegateInstanceRunning
from harness.session_delegate_running import SessionDelegateRunning
from harness.step_instance_execution import StepInstanceExecution
from harness.step_run_outcome import StepRunOutcome


"""
solid-name: SafeSessionDelegateInstanceRunner
solid-category: service
solid-spec: [SPEC-037]
solid-description: Executes one session-delegate instance and returns a correlated retryable outcome.
"""
class SafeSessionDelegateInstanceRunner(SessionDelegateInstanceRunning):
    def __init__(
        self,
        runner: SessionDelegateRunning,
        instruction_builder: DelegateInstructionBuilding,
    ) -> None:
        self._runner = runner
        self._instruction_builder = instruction_builder

    def run(self, instance: StepInstance) -> StepInstanceExecution:
        try:
            outcome = self._runner.run(
                self._instruction_builder.build(instance.prompt)
            )
        except Exception as error:
            outcome = StepRunOutcome(
                awaiting_input=False,
                rejection_reason=f"Delegated session failed: {error}",
            )
        return StepInstanceExecution(instance=instance, outcome=outcome)

"""Assembles the production run-state reconstruction pipeline."""

from harness.attempt_failed_transition import AttemptFailedTransition
from harness.run_state_builder import RunStateBuilder
from harness.run_state_event_router import RunStateEventRouter
from harness.run_state_reconstructor import RunStateReconstructor
from harness.run_status_transition import RunStatusTransition
from harness.step_completed_transition import StepCompletedTransition
from harness.step_outputs_builder import StepOutputsBuilder
from harness.step_rejected_transition import StepRejectedTransition
from harness.step_started_transition import StepStartedTransition
from harness.turn_counted_transition import TurnCountedTransition


def make_run_state_reconstructor() -> RunStateReconstructor:
    attempt_failed = AttemptFailedTransition()
    return RunStateReconstructor(
        state_builder=RunStateBuilder(),
        event_router=RunStateEventRouter(
            transitions={
                "step_started": StepStartedTransition(),
                "step_completed": StepCompletedTransition(step_outputs_builder=StepOutputsBuilder()),
                "turn_counted": TurnCountedTransition(),
                "run_completed": RunStatusTransition(status="done"),
                "run_timed_out": RunStatusTransition(status="timed_out"),
                "step_attempt_failed": attempt_failed,
                "step_rejected": StepRejectedTransition(attempt_transition=attempt_failed),
                "run_failed": RunStatusTransition(status="failed"),
            }
        ),
    )

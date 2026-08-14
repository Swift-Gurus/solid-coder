"""Attributes and handles failed workflow-step executions."""

from __future__ import annotations

from pathlib import Path

from harness.attempt_failure_handling import AttemptFailureHandling
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, RunState, StepDef, StepInstance
from harness.script_failure_attributing import ScriptFailureAttributing
from harness.step_execution_failure_handling import StepExecutionFailureHandling


"""
solid-name: StepExecutionFailureHandler
solid-category: service
solid-spec: [SPEC-010, SPEC-027]
solid-description: Attributes failed workflow executions and delegates attempt-state handling to the configured policy.
"""
class StepExecutionFailureHandler(StepExecutionFailureHandling):
    def __init__(
        self,
        failure_attributor: ScriptFailureAttributing,
        attempt_failure_handler: AttemptFailureHandling,
    ) -> None:
        self._failure_attributor = failure_attributor
        self._attempt_failure_handler = attempt_failure_handler

    def handle(
        self,
        reason: str,
        failed_step: StepDef,
        failed_instance: StepInstance,
        run_state: RunState,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
    ) -> FlowNextResult | None:
        target_step_id = self._failure_attributor.attribute(
            failed_step,
            run_state,
            flow_def,
        )
        return self._attempt_failure_handler.handle(
            step_id=target_step_id,
            reason=reason,
            reopen=target_step_id != failed_step.id,
            base_dir=base_dir,
            run_id=run_id,
            events_path=events_path,
            flow_def=flow_def,
            attempt_id=(
                failed_instance.instance_id
                if target_step_id == failed_step.id
                else None
            ),
        )

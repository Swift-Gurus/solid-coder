"""
solid-name: StepExecutionCoordinator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Executes ready steps repeatedly until the flow completes or cannot progress.
"""

from __future__ import annotations

from pathlib import Path

from harness.attempt_failure_handling import AttemptFailureHandling
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef
from harness.output_recording import OutputRecording
from harness.run_snapshot_resolving import RunSnapshotResolving
from harness.script_failure_attributing import ScriptFailureAttributing
from harness.step_execution_coordinating import StepExecutionCoordinating
from harness.step_handler_resolving import StepHandlerResolving

_ENGINE_SESSION_ID = "engine"


class StepExecutionCoordinator(StepExecutionCoordinating):

    def __init__(
        self,
        run_snapshot_resolver: RunSnapshotResolving,
        step_handler_resolver: StepHandlerResolving,
        failure_attributor: ScriptFailureAttributing,
        attempt_failure_handler: AttemptFailureHandling,
        output_recorder: OutputRecording,
    ) -> None:
        self._run_snapshot_resolver = run_snapshot_resolver
        self._step_handler_resolver = step_handler_resolver
        self._failure_attributor = failure_attributor
        self._attempt_failure_handler = attempt_failure_handler
        self._output_recorder = output_recorder

    def run_ready(
        self,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
        params: dict,
    ) -> FlowNextResult | None:
        step_map = {step.id: step for step in flow_def.steps}

        while True:
            snapshot = self._run_snapshot_resolver.resolve(events_path, flow_def, params)
            terminal, progressed = self._run_one_ready_instance(
                snapshot, step_map, base_dir, run_id, events_path, flow_def
            )
            if terminal is not None:
                return terminal
            if not progressed:
                return None

    def _run_one_ready_instance(self, snapshot, step_map, base_dir, run_id, events_path, flow_def):
        for instance in snapshot.ready:
            step_def = step_map[instance.step_id]
            handler = self._step_handler_resolver.resolve(step_def.type)
            outcome = handler.run(instance, step_def)
            if outcome.awaiting_input:
                continue

            if outcome.rejection_reason is not None:
                return self._handle_failure(
                    outcome.rejection_reason, step_def, snapshot, base_dir, run_id, events_path, flow_def
                ), True

            self._output_recorder.record(
                events_path, [instance], {instance.instance_id: outcome.outputs}, _ENGINE_SESSION_ID
            )
            return None, True

        return None, False

    def _handle_failure(self, reason, step_def, snapshot, base_dir, run_id, events_path, flow_def) -> FlowNextResult | None:
        target_step_id = self._failure_attributor.attribute(step_def, snapshot.run_state, flow_def)
        reopen = target_step_id != step_def.id
        return self._attempt_failure_handler.handle(
            step_id=target_step_id,
            reason=reason,
            reopen=reopen,
            base_dir=base_dir,
            run_id=run_id,
            events_path=events_path,
            flow_def=flow_def,
        )

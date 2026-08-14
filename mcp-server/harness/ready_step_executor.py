"""Executes or records one ready workflow-step instance."""

from __future__ import annotations

from harness.output_recording import OutputRecording
from harness.ready_step_executing import ReadyStepExecuting
from harness.ready_step_execution_outcome import ReadyStepExecutionOutcome
from harness.ready_step_execution_request import ReadyStepExecutionRequest
from harness.step_execution_failure_handling import StepExecutionFailureHandling
from harness.step_handler_resolving import StepHandlerResolving

_ENGINE_SESSION_ID = "engine"


"""
solid-name: ReadyStepExecutor
solid-category: service
solid-spec: [SPEC-010, SPEC-027]
solid-description: Executes one ready workflow instance, records validated outputs, and delegates execution failures.
"""
class ReadyStepExecutor(ReadyStepExecuting):
    def __init__(
        self,
        step_handler_resolver: StepHandlerResolving,
        failure_handler: StepExecutionFailureHandling,
        output_recorder: OutputRecording,
    ) -> None:
        self._step_handler_resolver = step_handler_resolver
        self._failure_handler = failure_handler
        self._output_recorder = output_recorder

    def execute(
        self,
        request: ReadyStepExecutionRequest,
    ) -> ReadyStepExecutionOutcome:
        for instance in request.snapshot.ready:
            if instance.automatic_outputs is not None:
                self._output_recorder.record(
                    request.events_path,
                    request.snapshot.ready,
                    {instance.instance_id: instance.automatic_outputs.to_dict()},
                    _ENGINE_SESSION_ID,
                )
                return ReadyStepExecutionOutcome(progressed=True)

            step_def = next(
                step
                for step in request.flow_def.steps
                if step.id == instance.step_id
            )
            handler = self._step_handler_resolver.resolve(step_def.type)
            outcome = handler.run(instance, step_def)
            if outcome.awaiting_input:
                continue

            if outcome.rejection_reason is not None:
                terminal = self._failure_handler.handle(
                    reason=outcome.rejection_reason,
                    failed_step=step_def,
                    failed_instance=instance,
                    run_state=request.snapshot.run_state,
                    base_dir=request.base_dir,
                    run_id=request.run_id,
                    events_path=request.events_path,
                    flow_def=request.flow_def,
                )
                return ReadyStepExecutionOutcome(
                    progressed=True,
                    terminal=terminal,
                )

            self._output_recorder.record(
                request.events_path,
                request.snapshot.ready,
                {instance.instance_id: outcome.outputs},
                _ENGINE_SESSION_ID,
            )
            return ReadyStepExecutionOutcome(progressed=True)

        return ReadyStepExecutionOutcome(progressed=False)

"""Validates and records engine-owned workflow-step execution batches."""

from __future__ import annotations

from harness.output_recording import OutputRecording
from harness.ready_step_execution_outcome import ReadyStepExecutionOutcome
from harness.step_execution_batch_advancing import StepExecutionBatchAdvancing
from harness.step_execution_batch_request import StepExecutionBatchRequest
from harness.step_execution_failure_handling import StepExecutionFailureHandling
from harness.step_instance_execution import StepInstanceExecution
from harness.step_run_outcome import StepRunOutcome
from harness.step_submission_validator_resolving import StepSubmissionValidatorResolving


_ENGINE_SESSION_ID = "engine"


"""
solid-name: StepExecutionBatchAdvancer
solid-category: service
solid-spec: [SPEC-037]
solid-description: Advances engine-owned workflow-step batches through validation, durable completion, and instance failure handling.
"""
class StepExecutionBatchAdvancer(StepExecutionBatchAdvancing):
    def __init__(
        self,
        validator_resolver: StepSubmissionValidatorResolving,
        output_recorder: OutputRecording,
        failure_handler: StepExecutionFailureHandling,
    ) -> None:
        self._validator_resolver = validator_resolver
        self._output_recorder = output_recorder
        self._failure_handler = failure_handler

    def advance(
        self,
        request: StepExecutionBatchRequest,
    ) -> ReadyStepExecutionOutcome:
        validator = self._validator_resolver.resolve(request.step_def.type)
        completed: list[StepInstanceExecution] = []
        failed: list[StepInstanceExecution] = []
        for execution in request.executions:
            outcome = execution.outcome
            if outcome.awaiting_input:
                continue
            if outcome.rejection_reason is not None or outcome.outputs is None:
                failed.append(execution)
                continue
            validation = validator.validate(
                execution.instance,
                outcome.outputs,
                request.ready_request.flow_def,
            )
            if validation.ok:
                completed.append(execution)
                continue
            failed.append(
                StepInstanceExecution(
                    instance=execution.instance,
                    outcome=StepRunOutcome(
                        awaiting_input=False,
                        rejection_reason="; ".join(validation.errors),
                    ),
                )
            )

        if completed:
            self._output_recorder.record(
                request.ready_request.events_path,
                request.ready_request.snapshot.ready,
                {
                    execution.instance.instance_id: execution.outcome.outputs
                    for execution in completed
                },
                _ENGINE_SESSION_ID,
            )

        if failed:
            terminal = self._failure_handler.handle_all(
                failures=failed,
                failed_step=request.step_def,
                run_state=request.ready_request.snapshot.run_state,
                base_dir=request.ready_request.base_dir,
                run_id=request.ready_request.run_id,
                events_path=request.ready_request.events_path,
                flow_def=request.ready_request.flow_def,
            )
            return ReadyStepExecutionOutcome(progressed=True, terminal=terminal)

        return ReadyStepExecutionOutcome(progressed=bool(completed))

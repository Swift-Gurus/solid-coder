"""Executes or records one ready workflow-step instance."""

from __future__ import annotations

from harness.ready_step_executing import ReadyStepExecuting
from harness.ready_step_execution_outcome import ReadyStepExecutionOutcome
from harness.ready_step_execution_request import ReadyStepExecutionRequest
from harness.output_recording import OutputRecording
from harness.step_batch_runner_resolving import StepBatchRunnerResolving
from harness.step_execution_batch_advancing import StepExecutionBatchAdvancing
from harness.step_execution_batch_request import StepExecutionBatchRequest

_ENGINE_SESSION_ID = "engine"


"""
solid-name: ReadyStepExecutor
solid-category: service
solid-spec: [SPEC-010, SPEC-027, SPEC-037]
solid-description: Coordinates batch execution of ready workflow-step instances and automatic empty completions.
"""
class ReadyStepExecutor(ReadyStepExecuting):
    def __init__(
        self,
        batch_runner_resolver: StepBatchRunnerResolving,
        batch_advancer: StepExecutionBatchAdvancing,
        output_recorder: OutputRecording,
    ) -> None:
        self._batch_runner_resolver = batch_runner_resolver
        self._batch_advancer = batch_advancer
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

        step_ids: list[str] = []
        for instance in request.snapshot.ready:
            if instance.step_id not in step_ids:
                step_ids.append(instance.step_id)
        for step_id in step_ids:
            step_def = next(step for step in request.flow_def.steps if step.id == step_id)
            instances = [
                instance
                for instance in request.snapshot.ready
                if instance.step_id == step_id
            ]
            executions = self._batch_runner_resolver.resolve(step_def).run_batch(
                instances,
                step_def,
            )
            outcome = self._batch_advancer.advance(
                StepExecutionBatchRequest(
                    ready_request=request,
                    step_def=step_def,
                    executions=executions,
                )
            )
            if outcome.progressed or outcome.terminal is not None:
                return outcome

        return ReadyStepExecutionOutcome(progressed=False)

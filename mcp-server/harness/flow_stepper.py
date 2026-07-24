"""
solid-name: FlowStepper
solid-category: service
solid-spec: [SPEC-013]
solid-description: Progresses a flow execution to the next step.
"""

from __future__ import annotations

from harness.active_run_locating import ActiveRunLocating
from harness.flow_loading import FlowLoading
from harness.flow_next_result import FlowNextResult
from harness.flow_stepping import FlowStepping
from harness.interpolation_error import InterpolationError
from harness.output_submission_advancing import OutputSubmissionAdvancing
from harness.ready_steps_resolving import ReadyStepsResolving
from harness.run_completion_checking import RunCompletionChecking
from harness.run_metadata_persisting import RunMetadataPersisting
from harness.run_snapshot_resolving import RunSnapshotResolving
from harness.step_execution_coordinating import StepExecutionCoordinating


class FlowStepper(FlowStepping):
    """
    solid-description: Progresses a flow execution to the next step.
    solid-category: service
    """

    def __init__(
        self,
        run_locator: ActiveRunLocating,
        metadata_store: RunMetadataPersisting,
        flow_loader: FlowLoading,
        run_snapshot_resolver: RunSnapshotResolving,
        submission_advancer: OutputSubmissionAdvancing,
        completion_checker: RunCompletionChecking,
        step_execution_coordinator: StepExecutionCoordinating,
        ready_steps_resolver: ReadyStepsResolving,
    ) -> None:
        self._run_locator = run_locator
        self._metadata_store = metadata_store
        self._flow_loader = flow_loader
        self._run_snapshot_resolver = run_snapshot_resolver
        self._submission_advancer = submission_advancer
        self._completion_checker = completion_checker
        self._step_execution_coordinator = step_execution_coordinator
        self._ready_steps_resolver = ready_steps_resolver

    def flow_next(self, outputs: dict | None = None, run_id: str | None = None) -> FlowNextResult:
        location = self._run_locator.locate(run_id)
        metadata = self._metadata_store.read(location.run_dir)
        flow_def = self._flow_loader.load(location.workflow_path, [])

        try:
            snapshot = self._run_snapshot_resolver.resolve(location.events_path, flow_def, metadata.params)
        except InterpolationError as exc:
            return FlowNextResult(status="ready", error=str(exc))

        outcome = self._submission_advancer.submit(
            location.events_path, location.base_dir, location.run_id, snapshot.ready, outputs or {}, flow_def
        )
        if outcome.terminal is not None:
            return outcome.terminal

        if outcome.run_state is not None:
            terminal = self._completion_checker.check(
                location.base_dir, location.run_id, location.events_path, flow_def, outcome.run_state
            )
            if terminal is not None:
                return terminal

        step_terminal = self._step_execution_coordinator.run_ready(
            location.base_dir, location.run_id, location.events_path, flow_def, metadata.params
        )
        if step_terminal is not None:
            return step_terminal

        try:
            steps = self._ready_steps_resolver.resolve(location.events_path, flow_def, metadata.params)
        except InterpolationError as exc:
            return FlowNextResult(status="ready", error=str(exc))
        return FlowNextResult(status="ready", steps=steps)

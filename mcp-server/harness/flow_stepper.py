"""
solid-name: FlowStepper
solid-category: service
solid-spec: [SPEC-031]
solid-description: Advances flow execution and determines the next ready steps based on submitted outputs.
"""

from __future__ import annotations

from harness.active_run_locating import ActiveRunLocating
from harness.execution_and_readiness_coordinating import ExecutionAndReadinessCoordinating
from harness.flow_loading import FlowLoading
from harness.flow_next_result import FlowNextResult
from harness.flow_stepping import FlowStepping
from harness.interpolation_guarding import InterpolationGuarding
from harness.output_submission_advancing import OutputSubmissionAdvancing
from harness.run_completion_checking import RunCompletionChecking
from harness.run_metadata_persisting import RunMetadataPersisting
from harness.run_snapshot_resolving import RunSnapshotResolving


class FlowStepper(FlowStepping):
    """
    solid-description: Advances flow execution and determines the next ready steps based on submitted outputs.
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
        execution_and_readiness_coordinator: ExecutionAndReadinessCoordinating,
        interpolation_guard: InterpolationGuarding,
    ) -> None:
        self._run_locator = run_locator
        self._metadata_store = metadata_store
        self._flow_loader = flow_loader
        self._run_snapshot_resolver = run_snapshot_resolver
        self._submission_advancer = submission_advancer
        self._completion_checker = completion_checker
        self._execution_and_readiness_coordinator = execution_and_readiness_coordinator
        self._interpolation_guard = interpolation_guard

    def flow_next(self, outputs: dict | None = None, run_id: str | None = None) -> FlowNextResult:
        location = self._run_locator.locate(run_id)
        metadata = self._metadata_store.read(location.run_dir)
        flow_def = self._flow_loader.load(location.workflow_path, [])

        snapshot, error = self._interpolation_guard.guard(
            lambda: self._run_snapshot_resolver.resolve(location.events_path, flow_def, metadata.params)
        )
        if error is not None:
            return FlowNextResult(status="ready", error=error)

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

        execution = self._execution_and_readiness_coordinator.coordinate(
            location.base_dir, location.run_id, location.events_path, flow_def, metadata.params
        )
        if execution.error is not None:
            return FlowNextResult(status="ready", error=execution.error)
        if execution.terminal is not None:
            return execution.terminal
        return FlowNextResult(status="ready", steps=execution.steps)

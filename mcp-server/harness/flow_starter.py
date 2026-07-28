"""
solid-name: FlowStarter
solid-category: service
solid-spec: [SPEC-013]
solid-description: Initializes a flow execution and determines which steps are ready to run.
"""

from __future__ import annotations

from harness.event_appender import EventAppending
from harness.flow_loading import FlowLoading
from harness.flow_start_result import FlowStartResult
from harness.flow_starting import FlowStarting
from harness.interpolation_error import InterpolationError
from harness.isolated_run_paths import ISOLATED_RUNS_DIRNAME
from harness.run_provisioning import RunProvisioning
from harness.run_snapshot_resolving import RunSnapshotResolving
from harness.startup_context_resolving import StartupContextResolving
from harness.step_execution_coordinating import StepExecutionCoordinating
from harness.step_result_building import StepResultBuilding


class FlowStarter(FlowStarting):
    """
    solid-description: Initializes a flow execution and determines which steps are ready to run.
    solid-category: service
    """

    def __init__(
        self,
        startup_context: StartupContextResolving,
        flow_loader: FlowLoading,
        run_provisioner: RunProvisioning,
        event_appender: EventAppending,
        run_snapshot_resolver: RunSnapshotResolving,
        step_result_builder: StepResultBuilding,
        step_execution_coordinator: StepExecutionCoordinating,
    ) -> None:
        self._startup_context = startup_context
        self._flow_loader = flow_loader
        self._run_provisioner = run_provisioner
        self._event_appender = event_appender
        self._run_snapshot_resolver = run_snapshot_resolver
        self._step_result_builder = step_result_builder
        self._step_execution_coordinator = step_execution_coordinator

    def flow_start(self, flow: str, params: dict | None = None, isolated: bool = False) -> FlowStartResult:
        params = params or {}
        startup = self._startup_context.resolve()
        flow_def = self._flow_loader.load(flow, startup.search_paths)

        base_dir = (startup.base_dir / ISOLATED_RUNS_DIRNAME) if isolated else startup.base_dir
        run_init = self._run_provisioner.provision(base_dir, flow_def, params, self_contained=isolated)
        effective_base_dir = run_init.run_dir if isolated else base_dir

        events_path = str(run_init.run_dir / "events.jsonl")
        self._event_appender.append(events_path, "run_started", {"run_id": run_init.run_id, "flow": flow_def.name})

        try:
            terminal = self._step_execution_coordinator.run_ready(
                effective_base_dir, run_init.run_id, events_path, flow_def, params
            )
        except InterpolationError as exc:
            return FlowStartResult(run_id=run_init.run_id, steps=[], error=str(exc))
        if terminal is not None:
            return FlowStartResult(run_id=run_init.run_id, steps=[], error="Run failed before any step could start")

        try:
            snapshot = self._run_snapshot_resolver.resolve(events_path, flow_def, params)
            steps = self._step_result_builder.build(snapshot.ready, flow_def, snapshot.run_state)
        except InterpolationError as exc:
            return FlowStartResult(run_id=run_init.run_id, steps=[], error=str(exc))
        return FlowStartResult(run_id=run_init.run_id, steps=steps, isolated=isolated)

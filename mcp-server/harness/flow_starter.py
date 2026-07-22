"""
solid-name: FlowStarter
solid-category: service
solid-spec: [SPEC-013]
solid-description: Starts a new flow run and returns the run identifier and its ready steps.
"""

from __future__ import annotations

from harness.event_appender import EventAppending
from harness.flow_loading import FlowLoading
from harness.flow_start_result import FlowStartResult
from harness.flow_starting import FlowStarting
from harness.interpolation_error import InterpolationError
from harness.run_provisioning import RunProvisioning
from harness.run_snapshot_resolving import RunSnapshotResolving
from harness.startup_context_resolving import StartupContextResolving
from harness.step_result_building import StepResultBuilding


class FlowStarter(FlowStarting):

    def __init__(
        self,
        startup_context: StartupContextResolving,
        flow_loader: FlowLoading,
        run_provisioner: RunProvisioning,
        event_appender: EventAppending,
        run_snapshot_resolver: RunSnapshotResolving,
        step_result_builder: StepResultBuilding,
    ) -> None:
        self._startup_context = startup_context
        self._flow_loader = flow_loader
        self._run_provisioner = run_provisioner
        self._event_appender = event_appender
        self._run_snapshot_resolver = run_snapshot_resolver
        self._step_result_builder = step_result_builder

    def flow_start(self, flow: str, params: dict | None = None) -> FlowStartResult:
        params = params or {}
        startup = self._startup_context.resolve()
        flow_def = self._flow_loader.load(flow, startup.search_paths)

        run_init = self._run_provisioner.provision(startup.base_dir, flow_def, params, startup.detected_env)

        events_path = str(run_init.run_dir / "events.jsonl")
        self._event_appender.append(events_path, "run_started", {"run_id": run_init.run_id, "flow": flow_def.name})

        try:
            snapshot = self._run_snapshot_resolver.resolve(events_path, flow_def, params)
            steps = self._step_result_builder.build(snapshot.ready, flow_def, startup.detected_env)
        except InterpolationError as exc:
            return FlowStartResult(run_id=run_init.run_id, steps=[], error=str(exc))
        return FlowStartResult(run_id=run_init.run_id, steps=steps)

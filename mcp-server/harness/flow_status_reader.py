"""
solid-name: FlowStatusReader
solid-category: service
solid-spec: [SPEC-013]
solid-description: Reads the current status of the active flow run.
"""

from __future__ import annotations

from harness.active_run_locating import ActiveRunLocating
from harness.flow_loading import FlowLoading
from harness.flow_status_reading import FlowStatusReading
from harness.flow_status_result import FlowStatusResult
from harness.interpolation_error import InterpolationError
from harness.run_snapshot_resolving import RunSnapshotResolving


class FlowStatusReader(FlowStatusReading):

    def __init__(
        self,
        run_locator: ActiveRunLocating,
        flow_loader: FlowLoading,
        run_snapshot_resolver: RunSnapshotResolving,
    ) -> None:
        self._run_locator = run_locator
        self._flow_loader = flow_loader
        self._run_snapshot_resolver = run_snapshot_resolver

    def flow_status(self) -> FlowStatusResult:
        try:
            location = self._run_locator.locate()
        except (FileNotFoundError, KeyError):
            return FlowStatusResult(
                flow="", run_id="", status="no_active_run",
                turn_count=0, max_turns=0,
                completed=[], running=[], pending=[],
            )

        flow_def = self._flow_loader.load(location.workflow_path, [])

        try:
            snapshot = self._run_snapshot_resolver.resolve(location.events_path, flow_def, {})
        except InterpolationError as exc:
            return FlowStatusResult(
                flow=flow_def.name, run_id=location.run_id, status="error",
                turn_count=0, max_turns=flow_def.max_turns,
                completed=[], running=[], pending=[], error=str(exc),
            )

        return FlowStatusResult(
            flow=flow_def.name,
            run_id=location.run_id,
            status=snapshot.run_state.status,
            turn_count=snapshot.run_state.turn_count,
            max_turns=flow_def.max_turns,
            completed=list(snapshot.run_state.completed.keys()),
            running=list(snapshot.run_state.running),
            pending=[i.step_id for i in snapshot.ready],
        )

"""
solid-description: Determines which flow steps are ready to execute based on the flow definition and execution history.
solid-category: service
"""

from __future__ import annotations

from harness.models import FlowDef
from harness.run_snapshot_resolving import RunSnapshotResolving
from harness.step_result import StepResult
from harness.step_result_building import StepResultBuilding


class ReadyStepsResolver:
    """
    solid-description: Determines which flow steps are ready to execute based on the flow definition and execution history.
    solid-category: service
    """

    def __init__(
        self,
        run_snapshot_resolver: RunSnapshotResolving,
        step_result_builder: StepResultBuilding,
    ) -> None:
        self._run_snapshot_resolver = run_snapshot_resolver
        self._step_result_builder = step_result_builder

    def resolve(self, events_path: str, flow_def: FlowDef, params: dict) -> list[StepResult]:
        snapshot = self._run_snapshot_resolver.resolve(events_path, flow_def, params)
        return self._step_result_builder.build(snapshot.ready, flow_def, snapshot.run_state)

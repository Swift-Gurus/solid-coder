"""
solid-name: RunSnapshotResolver
solid-category: service
solid-spec: [SPEC-013]
solid-description: Resolves the current execution state and ready steps of a flow run.
"""

from __future__ import annotations

from harness.dag_running import DAGRunning
from harness.event_replaying import EventReplaying
from harness.models import FlowDef
from harness.run_context_building import RunContextBuilding
from harness.run_snapshot import RunSnapshot


class RunSnapshotResolver:

    def __init__(
        self,
        event_replayer: EventReplaying,
        context_builder: RunContextBuilding,
        dag_runner: DAGRunning,
    ) -> None:
        self._event_replayer = event_replayer
        self._context_builder = context_builder
        self._dag_runner = dag_runner

    def resolve(self, events_path: str, flow_def: FlowDef, params: dict) -> RunSnapshot:
        run_state = self._event_replayer.replay(events_path)
        context = self._context_builder.build(params, run_state)
        ready = self._dag_runner.ready_steps(flow_def, run_state, context)
        return RunSnapshot(run_state=run_state, ready=ready)
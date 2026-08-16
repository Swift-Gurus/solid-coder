"""Resolves one workflow-run snapshot."""

from __future__ import annotations

from dataclasses import replace

from harness.dag_running import DAGRunning
from harness.dynamic_workflow_steps_resolving import DynamicWorkflowStepsResolving
from harness.event_replaying import EventReplaying
from harness.models import FlowDef
from harness.run_context_building import RunContextBuilding
from harness.run_snapshot import RunSnapshot
from harness.run_snapshot_resolving import RunSnapshotResolving


"""
solid-name: RunSnapshotResolver
solid-category: service
solid-spec: [SPEC-031, SPEC-037]
solid-description: Resolves run state, the executable workflow definition, and ready instances as one consistent snapshot.
"""
class RunSnapshotResolver(RunSnapshotResolving):

    def __init__(
        self,
        event_replayer: EventReplaying,
        context_builder: RunContextBuilding,
        step_resolver: DynamicWorkflowStepsResolving,
        dag_runner: DAGRunning,
    ) -> None:
        self._event_replayer = event_replayer
        self._context_builder = context_builder
        self._step_resolver = step_resolver
        self._dag_runner = dag_runner

    def resolve(self, events_path: str, flow_def: FlowDef, params: dict) -> RunSnapshot:
        run_state = self._event_replayer.replay(events_path)
        context = self._context_builder.build(params, run_state)
        executable_flow = replace(
            flow_def,
            steps=self._step_resolver.resolve(flow_def, run_state, context),
        )
        ready = self._dag_runner.ready_steps(executable_flow, run_state, context)
        return RunSnapshot(
            run_state=run_state,
            flow_def=executable_flow,
            ready=ready,
        )

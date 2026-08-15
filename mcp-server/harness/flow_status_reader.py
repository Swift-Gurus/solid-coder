"""Reads current workflow-run status."""

from __future__ import annotations

from harness.active_run_locating import ActiveRunLocating
from harness.condition_serializing import ConditionSerializing
from harness.flow_loading import FlowLoading
from harness.flow_status_reading import FlowStatusReading
from harness.flow_status_result import FlowStatusResult
from harness.interpolation_error import InterpolationError
from harness.run_snapshot_resolving import RunSnapshotResolving
from harness.step_skip_status import StepSkipStatus
from harness.workflow_condition_status import WorkflowConditionStatus


"""
solid-name: FlowStatusReader
solid-category: service
solid-spec: [SPEC-031, SPEC-037]
solid-description: Reads execution, skip, and workflow eligibility state for a flow run.
"""
class FlowStatusReader(FlowStatusReading):

    def __init__(
        self,
        run_locator: ActiveRunLocating,
        flow_loader: FlowLoading,
        run_snapshot_resolver: RunSnapshotResolving,
        condition_serializer: ConditionSerializing,
    ) -> None:
        self._run_locator = run_locator
        self._flow_loader = flow_loader
        self._run_snapshot_resolver = run_snapshot_resolver
        self._condition_serializer = condition_serializer

    def flow_status(self, run_id: str | None = None) -> FlowStatusResult:
        try:
            location = self._run_locator.locate(run_id)
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

        workflow_decision = snapshot.run_state.workflow_condition_decision
        workflow_condition = (
            WorkflowConditionStatus(
                matched=workflow_decision.matched,
                condition=self._condition_serializer.serialize(
                    workflow_decision.condition
                ),
            )
            if workflow_decision is not None
            else None
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
            skipped=[
                StepSkipStatus(
                    step_id=skip.step_id,
                    instance_id=skip.instance_id,
                    condition=self._condition_serializer.serialize(skip.condition),
                    item=skip.item,
                    iteration_index=skip.iteration_index,
                )
                for skip in snapshot.run_state.skipped_instances.values()
            ],
            workflow_condition=workflow_condition,
        )

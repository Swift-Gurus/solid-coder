"""Drains consecutive engine-executable workflow steps."""

from __future__ import annotations

from pathlib import Path

from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef
from harness.ready_step_executing import ReadyStepExecuting
from harness.ready_step_execution_request import ReadyStepExecutionRequest
from harness.run_snapshot_resolving import RunSnapshotResolving
from harness.step_execution_coordinating import StepExecutionCoordinating


"""
solid-name: EngineStepDrainer
solid-category: service
solid-spec: [SPEC-010, SPEC-027]
solid-description: Drains consecutive engine-executable workflow instances until input, failure, or no progress.
"""
class EngineStepDrainer(StepExecutionCoordinating):
    def __init__(
        self,
        run_snapshot_resolver: RunSnapshotResolving,
        ready_step_executor: ReadyStepExecuting,
    ) -> None:
        self._run_snapshot_resolver = run_snapshot_resolver
        self._ready_step_executor = ready_step_executor

    def run_ready(
        self,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
        params: dict,
    ) -> FlowNextResult | None:
        while True:
            snapshot = self._run_snapshot_resolver.resolve(
                events_path,
                flow_def,
                params,
            )
            outcome = self._ready_step_executor.execute(
                ReadyStepExecutionRequest(
                    snapshot=snapshot,
                    base_dir=base_dir,
                    run_id=run_id,
                    events_path=events_path,
                    flow_def=flow_def,
                )
            )
            if outcome.terminal is not None:
                return outcome.terminal
            if not outcome.progressed:
                return None

"""Defines failure handling for one executed workflow step."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, RunState, StepDef
from harness.step_instance_execution import StepInstanceExecution


"""
solid-name: StepExecutionFailureHandling
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-027]
solid-description: Contract for attributing and handling one failed workflow-step execution.
"""
class StepExecutionFailureHandling(Protocol):
    def handle_all(
        self,
        failures: list[StepInstanceExecution],
        failed_step: StepDef,
        run_state: RunState,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
    ) -> FlowNextResult | None: ...

"""Defines failure handling for one executed workflow step."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, RunState, StepDef, StepInstance


"""
solid-name: StepExecutionFailureHandling
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-027]
solid-description: Contract for attributing and handling one failed workflow-step execution.
"""
class StepExecutionFailureHandling(Protocol):
    def handle(
        self,
        reason: str,
        failed_step: StepDef,
        failed_instance: StepInstance,
        run_state: RunState,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
    ) -> FlowNextResult | None: ...

"""
solid-name: ExecutionAndReadinessCoordinating
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for coordinating a flow's execution and readiness state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.execution_outcome import ExecutionOutcome
from harness.models import FlowDef


class ExecutionAndReadinessCoordinating(Protocol):
    def coordinate(
        self,
        effective_base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
        params: dict,
    ) -> ExecutionOutcome: ...

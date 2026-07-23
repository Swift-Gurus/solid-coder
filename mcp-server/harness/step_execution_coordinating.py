"""
solid-name: StepExecutionCoordinating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for automatically driving steps to completion or failure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef


class StepExecutionCoordinating(Protocol):

    def run_ready(
        self,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
        params: dict,
    ) -> FlowNextResult | None: ...

"""
solid-name: RunCompletionChecking
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for determining whether a run has reached its terminal state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, RunState


class RunCompletionChecking(Protocol):

    def check(
        self,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
        run_state: RunState,
    ) -> FlowNextResult | None: ...
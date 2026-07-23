"""
solid-name: AttemptFailureHandling
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for handling a failed step attempt by optionally reopening the step and determining the flow's next state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef


class AttemptFailureHandling(Protocol):

    def handle(
        self,
        step_id: str,
        reason: str,
        reopen: bool,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
    ) -> FlowNextResult | None: ...
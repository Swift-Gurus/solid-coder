"""Defines batch attempt-failure handling."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.attempt_failure import AttemptFailure
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef


"""
solid-name: AttemptFailuresHandling
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-037]
solid-description: Contract for durably recording an attempt-failure batch before evaluating run completion.
"""
class AttemptFailuresHandling(Protocol):
    def handle_all(
        self,
        failures: list[AttemptFailure],
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
    ) -> FlowNextResult | None: ...

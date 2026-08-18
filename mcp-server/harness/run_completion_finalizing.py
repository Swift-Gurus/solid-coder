"""Defines work performed immediately before a workflow run is completed."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.flow_def import FlowDef
from harness.run_state import RunState


"""
solid-name: RunCompletionFinalizing
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for publishing deterministic artifacts before a workflow run is marked complete.
"""
class RunCompletionFinalizing(Protocol):
    def finalize(
        self,
        run_directory: Path,
        events_path: str,
        flow_def: FlowDef,
        run_state: RunState,
    ) -> None: ...

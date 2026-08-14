"""Defines the context required to execute one ready workflow step."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harness.models import FlowDef
from harness.run_snapshot import RunSnapshot


"""
solid-name: ReadyStepExecutionRequest
solid-category: model
solid-spec: [SPEC-010, SPEC-027]
solid-description: Carries run location, workflow definition, and snapshot state for one ready-step execution attempt.
"""
@dataclass(frozen=True)
class ReadyStepExecutionRequest:
    snapshot: RunSnapshot
    base_dir: Path
    run_id: str
    events_path: str
    flow_def: FlowDef

"""Defines construction of workflow-timeout diagnostics."""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef, RunState


"""
solid-name: RunTimeoutMessageBuilding
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-031]
solid-description: Contract for constructing a workflow-run timeout diagnostic.
"""
class RunTimeoutMessageBuilding(Protocol):
    def build(
        self,
        flow_def: FlowDef,
        run_state: RunState,
        events_path: str,
    ) -> str: ...

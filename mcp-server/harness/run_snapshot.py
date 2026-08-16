"""Defines one resolved workflow-run snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.models import FlowDef, RunState, StepInstance


"""
solid-name: RunSnapshot
solid-category: model
solid-spec: [SPEC-031, SPEC-037]
solid-description: Captures run state, its executable workflow definition, and the ready instances derived from that same definition.
"""
@dataclass(frozen=True)
class RunSnapshot:
    run_state: RunState
    flow_def: FlowDef
    ready: list[StepInstance] = field(default_factory=list)

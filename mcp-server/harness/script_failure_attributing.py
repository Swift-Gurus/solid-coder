"""
solid-name: ScriptFailureAttributing
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract that defines how to attribute script failures to appropriate steps.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef, RunState, StepDef


class ScriptFailureAttributing(Protocol):

    def attribute(self, failed_step: StepDef, run_state: RunState, flow_def: FlowDef) -> str: ...

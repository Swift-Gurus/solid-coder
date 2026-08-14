"""Constructs workflow-timeout diagnostics."""

from __future__ import annotations

from harness.models import FlowDef, RunState
from harness.run_timeout_message_building import RunTimeoutMessageBuilding


"""
solid-name: RunTimeoutMessageBuilder
solid-category: service
solid-spec: [SPEC-010, SPEC-031]
solid-description: Constructs an actionable diagnostic for a workflow run that reaches its turn limit.
"""
class RunTimeoutMessageBuilder(RunTimeoutMessageBuilding):
    def build(
        self,
        flow_def: FlowDef,
        run_state: RunState,
        events_path: str,
    ) -> str:
        pending = ", ".join(run_state.running) or "none"
        return (
            f"Flow timed out — reached the flow's max_turns limit ({flow_def.max_turns} turns) with step(s) "
            f"still pending: {pending}. Full run log: {events_path}. Stop here — do not retry or continue this "
            "flow. Report this to the user and wait for their instructions."
        )

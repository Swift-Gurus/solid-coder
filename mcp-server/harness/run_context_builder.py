"""
solid-name: RunContextBuilder
solid-category: service
solid-spec: [SPEC-013]
solid-description: Assembles run parameters and run state data into a context dictionary.
"""

from __future__ import annotations

from typing import Any

from harness.models import RunState
from harness.run_context_building import RunContextBuilding


class RunContextBuilder:

    def build(self, params: dict, run_state: RunState) -> dict[str, Any]:
        steps_context: dict[str, Any] = {
            step_id: step_outputs
            for step_id, step_outputs in run_state.completed.items()
        }
        return {
            "params": params,
            "steps": steps_context,
            "rejection_reasons": dict(run_state.rejection_reasons),
            "attempts_used": dict(run_state.attempts_used),
        }

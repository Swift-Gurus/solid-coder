"""
solid-name: RunContextBuilder
solid-category: service
solid-spec: [SPEC-013]
solid-description: Builds the template interpolation context from run params and completed step outputs.
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
        return {"params": params, "steps": steps_context}

"""solid-name: FlowResultJsonRenderer
solid-category: service
solid-spec: [SPEC-031]
solid-description: Renders flow execution results as structured JSON strings.
"""

from __future__ import annotations

import dataclasses
import json

from harness.flow_next_result import FlowNextResult
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_start_result import FlowStartResult


class FlowResultJsonRenderer(FlowResultRendering):

    def __init__(self, flat_renderer: FlowResultRendering | None = None) -> None:
        self._flat_renderer = flat_renderer

    def render_start(self, result: FlowStartResult) -> str:
        if result.steps and result.steps[0].submission_id is not None:
            if self._flat_renderer is None:
                raise ValueError("Flat JSON responses require an instruction renderer")
            return json.dumps({"run_id": result.run_id, "status": result.status,
                               "instructions": self._flat_renderer.render_start(result)})
        return json.dumps(dataclasses.asdict(result))

    def render_next(self, result: FlowNextResult) -> str:
        if result.steps and result.steps[0].submission_id is not None:
            if self._flat_renderer is None:
                raise ValueError("Flat JSON responses require an instruction renderer")
            return json.dumps({"status": result.status,
                               "instructions": self._flat_renderer.render_next(result)})
        return json.dumps(dataclasses.asdict(result))

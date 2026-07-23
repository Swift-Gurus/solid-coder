"""solid-name: FlowResultJsonRenderer
solid-category: service
solid-spec: [SPEC-013]
solid-description: Renders flow execution results as structured JSON strings.
"""

from __future__ import annotations

import dataclasses
import json

from harness.flow_next_result import FlowNextResult
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_start_result import FlowStartResult


class FlowResultJsonRenderer(FlowResultRendering):

    def render_start(self, result: FlowStartResult) -> str:
        return json.dumps(dataclasses.asdict(result))

    def render_next(self, result: FlowNextResult) -> str:
        return json.dumps(dataclasses.asdict(result))
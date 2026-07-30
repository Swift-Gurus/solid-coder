"""
solid-name: FlowStartResultBuilder
solid-category: service
solid-spec: [SPEC-013]
solid-description: Produces a structured result representing a run's execution state and completion status.
"""

from __future__ import annotations

from harness.execution_outcome import ExecutionOutcome
from harness.flow_start_result import FlowStartResult
from harness.flow_start_result_building import FlowStartResultBuilding


class FlowStartResultBuilder(FlowStartResultBuilding):

    def build(self, run_id: str, outcome: ExecutionOutcome, isolated: bool) -> FlowStartResult:
        if outcome.error is not None:
            return FlowStartResult(run_id=run_id, steps=[], error=outcome.error)
        if outcome.terminal is not None:
            return FlowStartResult(run_id=run_id, steps=[], error=outcome.terminal.error, status=outcome.terminal.status)
        return FlowStartResult(run_id=run_id, steps=outcome.steps, isolated=isolated)

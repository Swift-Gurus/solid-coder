"""Builds typed workflow runtime context."""

from __future__ import annotations

from harness.models import RunState
from harness.run_context_building import RunContextBuilding
from harness.workflow_context_values_mapping import WorkflowContextValuesMapping
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: RunContextBuilder
solid-category: service
solid-spec: [SPEC-031, SPEC-037]
solid-description: Assembles run parameters and replayed state into typed workflow runtime context.
"""
class RunContextBuilder(RunContextBuilding):
    def __init__(self, values_mapper: WorkflowContextValuesMapping) -> None:
        self._values_mapper = values_mapper

    def build(self, params: dict, run_state: RunState) -> WorkflowRunContext:
        return WorkflowRunContext(
            parameters=self._values_mapper.map(params),
            completed_steps=self._values_mapper.map(run_state.completed),
            rejection_reasons=self._values_mapper.map(
                run_state.rejection_reasons
            ),
            attempts_used=self._values_mapper.map(run_state.attempts_used),
        )

"""Defines advancement of workflow-level condition state."""

from __future__ import annotations

from typing import Protocol

from harness.flow_def import FlowDef
from harness.run_state import RunState
from harness.workflow_condition_gate_result import WorkflowConditionGateResult


"""
solid-name: WorkflowConditionAdvancing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for advancing durable workflow-level condition state before step execution.
"""
class WorkflowConditionAdvancing(Protocol):
    def advance(
        self,
        events_path: str,
        flow_def: FlowDef,
        params: dict,
        run_state: RunState,
    ) -> WorkflowConditionGateResult: ...

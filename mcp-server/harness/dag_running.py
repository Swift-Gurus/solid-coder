"""Defines internal ready-step instance resolution."""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef, RunState, StepInstance
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: DAGRunning
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for resolving executable step instances from replayed run state and typed runtime context.
"""
class DAGRunning(Protocol):
    def ready_steps(
        self,
        flow_def: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> list[StepInstance]: ...

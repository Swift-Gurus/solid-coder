"""Defines runtime resolution of executable workflow steps."""

from __future__ import annotations

from typing import Protocol

from harness.dynamic_workflow_materialization import DynamicWorkflowMaterialization
from harness.models import FlowDef, RunState
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: DynamicWorkflowStepsResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving static and dynamic workflow declarations into executable steps and runtime groups.
"""
class DynamicWorkflowStepsResolving(Protocol):
    def resolve(
        self,
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> DynamicWorkflowMaterialization: ...

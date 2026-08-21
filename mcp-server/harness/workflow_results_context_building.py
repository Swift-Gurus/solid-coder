"""Defines construction of included-workflow result context."""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef, RunState
from harness.workflow_alias_results import WorkflowAliasResults
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowResultsContextBuilding
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for constructing ordered included-workflow results from executable run state.
"""
class WorkflowResultsContextBuilding(Protocol):
    def build(
        self,
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> WorkflowContextValues[WorkflowAliasResults]: ...

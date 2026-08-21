"""Defines construction of one included-workflow result envelope."""

from __future__ import annotations

from typing import Protocol

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import RunState
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.workflow_output_declaration import WorkflowOutputDeclaration
from harness.workflow_result_envelope import WorkflowResultEnvelope
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowResultEnvelopeBuilding
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for constructing a published result from one terminal included-workflow instance.
"""
class WorkflowResultEnvelopeBuilding(Protocol):
    def build(
        self,
        instance: IncludedWorkflowInstance,
        outputs: list[WorkflowOutputDeclaration],
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> ResolvedWorkflowContextValue[WorkflowResultEnvelope]: ...

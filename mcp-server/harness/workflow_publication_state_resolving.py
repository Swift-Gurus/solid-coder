"""Defines publication-state resolution for workflow instances."""

from __future__ import annotations

from typing import Protocol

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import RunState
from harness.workflow_publication_state import WorkflowPublicationState


"""
solid-name: WorkflowPublicationStateResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving whether an included-workflow result is pending, omitted, or publishable.
"""
class WorkflowPublicationStateResolving(Protocol):
    def resolve(
        self,
        instance: IncludedWorkflowInstance,
        run_state: RunState,
    ) -> WorkflowPublicationState: ...

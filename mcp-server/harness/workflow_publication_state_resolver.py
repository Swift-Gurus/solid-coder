"""Resolves publication state for included-workflow results."""

from __future__ import annotations

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import RunState
from harness.step_terminal_state import StepTerminalState
from harness.step_terminal_state_resolving import StepTerminalStateResolving
from harness.workflow_publication_state import WorkflowPublicationState
from harness.workflow_publication_state_resolving import (
    WorkflowPublicationStateResolving,
)


"""
solid-name: WorkflowPublicationStateResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves whether an included-workflow result is pending, omitted, or publishable.
"""
class WorkflowPublicationStateResolver(WorkflowPublicationStateResolving):

    def __init__(
        self,
        terminal_state_resolver: StepTerminalStateResolving,
    ) -> None:
        self._terminal_state_resolver = terminal_state_resolver

    def resolve(
        self,
        instance: IncludedWorkflowInstance,
        run_state: RunState,
    ) -> WorkflowPublicationState:
        terminal_states = [
            self._terminal_state_resolver.resolve(
                identity.execution_step_id,
                run_state,
            )
            for identity in instance.steps.entries
        ]
        if any(state is StepTerminalState.PENDING for state in terminal_states):
            return WorkflowPublicationState.PENDING
        if terminal_states and all(
            state is StepTerminalState.SKIPPED
            for state in terminal_states
        ):
            return WorkflowPublicationState.OMITTED
        return WorkflowPublicationState.PUBLISHABLE

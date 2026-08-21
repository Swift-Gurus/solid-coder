"""Builds one included-workflow result envelope."""

from __future__ import annotations

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import RunState
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.workflow_output_declaration import WorkflowOutputDeclaration
from harness.workflow_output_values_resolving import WorkflowOutputValuesResolving
from harness.workflow_publication_state import WorkflowPublicationState
from harness.workflow_publication_state_resolving import (
    WorkflowPublicationStateResolving,
)
from harness.workflow_result_envelope import WorkflowResultEnvelope
from harness.workflow_result_envelope_building import WorkflowResultEnvelopeBuilding
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowResultEnvelopeBuilder
solid-category: service
solid-spec: [SPEC-037]
solid-description: Builds the published result envelope for one included-workflow instance.
"""
class WorkflowResultEnvelopeBuilder(WorkflowResultEnvelopeBuilding):

    def __init__(
        self,
        publication_state_resolver: WorkflowPublicationStateResolving,
        output_values_resolver: WorkflowOutputValuesResolving,
    ) -> None:
        self._publication_state_resolver = publication_state_resolver
        self._output_values_resolver = output_values_resolver

    def build(
        self,
        instance: IncludedWorkflowInstance,
        outputs: list[WorkflowOutputDeclaration],
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> ResolvedWorkflowContextValue[WorkflowResultEnvelope]:
        publication_state = self._publication_state_resolver.resolve(
            instance,
            run_state,
        )
        if publication_state is not WorkflowPublicationState.PUBLISHABLE:
            return ResolvedWorkflowContextValue(present=False)
        return ResolvedWorkflowContextValue(
            present=True,
            value=WorkflowResultEnvelope(
                instance_id=instance.instance_id,
                item=instance.source_item,
                outputs=self._output_values_resolver.resolve(
                    instance,
                    outputs,
                    context,
                ),
            ),
        )

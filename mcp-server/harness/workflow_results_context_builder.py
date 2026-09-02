"""Builds included-workflow results for runtime expressions."""

from __future__ import annotations

from harness.included_workflow_instances_resolving import (
    IncludedWorkflowInstancesResolving,
)
from harness.models import FlowDef, RunState
from harness.workflow_alias_results import WorkflowAliasResults
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_result_envelope_building import WorkflowResultEnvelopeBuilding
from harness.workflow_results_context_building import WorkflowResultsContextBuilding
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowResultsContextBuilder
solid-category: service
solid-spec: [SPEC-037]
solid-description: Builds ordered include-alias results for workflow runtime expressions.
"""
class WorkflowResultsContextBuilder(WorkflowResultsContextBuilding):

    def __init__(
        self,
        instances_resolver: IncludedWorkflowInstancesResolving,
        envelope_builder: WorkflowResultEnvelopeBuilding,
    ) -> None:
        self._instances_resolver = instances_resolver
        self._envelope_builder = envelope_builder

    def build(
        self,
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> WorkflowContextValues[WorkflowAliasResults]:
        aliases: list[WorkflowContextValue[WorkflowAliasResults]] = []
        for group in flow.alias_groups:
            results = []
            for instance in self._instances_resolver.resolve(flow, group.alias):
                envelope = self._envelope_builder.build(
                    instance,
                    group.outputs,
                    run_state,
                    context,
                )
                if envelope.present and envelope.value is not None:
                    results.append(envelope.value)
            aliases.append(WorkflowContextValue(
                name=group.alias,
                value=WorkflowAliasResults(
                    authored_alias=group.authored_alias,
                    owner_alias=group.owner_alias,
                    runtime_owner_instance_id=group.runtime_owner_instance_id,
                    entries=results,
                ),
            ))
        return WorkflowContextValues(entries=aliases)

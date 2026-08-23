"""Resolves the nested runtime context visible to one workflow step."""

from __future__ import annotations

from dataclasses import replace

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolving import WorkflowStepContextResolving


"""
solid-name: WorkflowStepContextResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-037]
solid-description: Resolves root or included-workflow parameters, completed outputs, and item visibility for one executable step.
"""
class WorkflowStepContextResolver(WorkflowStepContextResolving):

    def resolve(
        self,
        context: WorkflowRunContext,
        workflow_instance: IncludedWorkflowInstance | None,
        item: object,
    ) -> WorkflowRunContext:
        if workflow_instance is None:
            return replace(
                context,
                item=ResolvedWorkflowContextValue(present=True, value=item),
            )

        local_completions = []
        local_skips = []
        for identity in workflow_instance.steps.entries:
            completed = context.completed_steps.find(identity.execution_step_id)
            if completed.present and completed.value is not None:
                local_completions.append(
                    WorkflowContextValue(
                        name=identity.local_step_id,
                        value=completed.value,
                    )
                )
            skipped = context.skipped_steps.find(identity.execution_step_id)
            if skipped.present and skipped.value is not None:
                local_skips.append(
                    WorkflowContextValue(
                        name=identity.local_step_id,
                        value=skipped.value,
                    )
                )
        return replace(
            context,
            parameters=workflow_instance.inputs,
            completed_steps=WorkflowContextValues(entries=local_completions),
            skipped_steps=WorkflowContextValues(entries=local_skips),
            item=ResolvedWorkflowContextValue(present=True, value=item),
        )

"""Materializes one item-scoped included workflow DAG."""

from __future__ import annotations

from dataclasses import replace
from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_dependencies_resolving import (
    IncludedWorkflowDependenciesResolving,
)
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.included_workflow_step_identity_resolving import (
    IncludedWorkflowStepIdentityResolving,
)
from harness.included_workflow_steps_resolving import IncludedWorkflowStepsResolving
from harness.models import StepDef
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.workflow_input_bindings_resolving import WorkflowInputBindingsResolving
from harness.workflow_run_context import WorkflowRunContext

"""
solid-name: IncludedWorkflowStepsResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Materializes qualified child workflow steps for one mapped source item.
"""
class IncludedWorkflowStepsResolver(IncludedWorkflowStepsResolving):

    def __init__(
        self,
        input_resolver: WorkflowInputBindingsResolving,
        identity_resolver: IncludedWorkflowStepIdentityResolving,
        dependency_resolver: IncludedWorkflowDependenciesResolving,
    ) -> None:
        self._input_resolver = input_resolver
        self._identity_resolver = identity_resolver
        self._dependency_resolver = dependency_resolver

    def resolve(
        self,
        group: IncludeAliasGroup,
        templates: list[StepDef],
        iteration_index: int,
        item: object,
        context: WorkflowRunContext,
    ) -> list[StepDef]:
        item_context = replace(
            context,
            item=ResolvedWorkflowContextValue(present=True, value=item),
        )
        child_inputs = self._input_resolver.resolve(
            group.input_bindings,
            item_context,
        )
        instance_prefix = f"{group.alias}-{iteration_index + 1}"
        step_identities = IncludedWorkflowStepIdentities(
            entries=[
                self._identity_resolver.resolve(
                    template.id,
                    group.alias,
                    instance_prefix,
                )
                for template in templates
            ]
        )
        workflow_instance = IncludedWorkflowInstance(
            alias=group.alias,
            instance_id=instance_prefix,
            source_index=iteration_index,
            source_item=item,
            owner_instance_id=group.runtime_owner_instance_id,
            condition=group.condition,
            inputs=child_inputs,
            steps=step_identities,
            rule_workflow=group.rule_workflow,
            for_each=group.for_each,
        )
        return [
            replace(
                template,
                id=step_identities.require_declaration(
                    template.id
                ).execution_step_id,
                depends_on=self._dependency_resolver.resolve(
                    template,
                    group,
                    step_identities,
                ),
                workflow_instance=workflow_instance,
            )
            for template in templates
        ]

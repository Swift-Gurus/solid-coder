"""Materializes one item-scoped included workflow DAG."""

from __future__ import annotations

from dataclasses import replace
from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_dependencies_resolving import (
    IncludedWorkflowDependenciesResolving,
)
from harness.included_workflow_identifier_qualifying import (
    IncludedWorkflowIdentifierQualifying,
)
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.included_workflow_steps_resolving import IncludedWorkflowStepsResolving
from harness.interpolator import TemplateRendering
from harness.models import StepDef
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
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
        identifier_qualifier: IncludedWorkflowIdentifierQualifying,
        dependency_resolver: IncludedWorkflowDependenciesResolving,
        renderer: TemplateRendering,
    ) -> None:
        self._input_resolver = input_resolver
        self._identifier_qualifier = identifier_qualifier
        self._dependency_resolver = dependency_resolver
        self._renderer = renderer

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
        resolved_inputs = self._input_resolver.resolve(
            group.input_bindings,
            item_context,
        )
        child_context = replace(
            item_context,
            parameters=WorkflowContextValues(
                entries=[
                    WorkflowContextValue(
                        name=resolved_input.name,
                        value=resolved_input.value,
                    )
                    for resolved_input in resolved_inputs
                ]
            ),
        )
        instance_prefix = f"{group.alias}-{iteration_index + 1}"
        workflow_instance = IncludedWorkflowInstance(
            alias=group.alias,
            instance_id=instance_prefix,
            source_index=iteration_index,
            source_item=item,
        )
        return [
            replace(
                template,
                id=self._identifier_qualifier.qualify(
                    template.id,
                    group.alias,
                    instance_prefix,
                ),
                prompt=self._renderer.render(template.prompt, child_context),
                depends_on=self._dependency_resolver.resolve(
                    template,
                    group,
                    instance_prefix,
                ),
                workflow_instance=workflow_instance,
            )
            for template in templates
        ]

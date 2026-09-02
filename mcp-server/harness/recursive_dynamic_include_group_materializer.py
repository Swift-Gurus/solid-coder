"""Materializes one dynamic include group and its owned descendants."""

from __future__ import annotations

from dataclasses import replace

from harness.dynamic_include_group_materializing import DynamicIncludeGroupMaterializing
from harness.for_each_items_resolving import ForEachItemsResolving
from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_readiness_checking import IncludeGroupReadinessChecking
from harness.include_group_runtime import IncludeGroupRuntime
from harness.include_group_runtime_rebasing import IncludeGroupRuntimeRebasing
from harness.include_group_templates_selecting import IncludeGroupTemplatesSelecting
from harness.include_group_tree_materialization import IncludeGroupTreeMaterialization
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.included_workflow_steps_resolving import IncludedWorkflowStepsResolving
from harness.materialized_workflow_instances_collecting import (
    MaterializedWorkflowInstancesCollecting,
)
from harness.models import FlowDef, RunState, StepDef
from harness.owned_include_dependencies_rebasing import (
    OwnedIncludeDependenciesRebasing,
)
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolving import WorkflowStepContextResolving


"""
solid-name: RecursiveDynamicIncludeGroupMaterializer
solid-category: service
solid-spec: [SPEC-037]
solid-description: Materializes one dynamic include group and recursively expands descendants for each parent instance.
"""
class RecursiveDynamicIncludeGroupMaterializer(
    DynamicIncludeGroupMaterializing
):
    def __init__(
        self,
        readiness_checker: IncludeGroupReadinessChecking,
        items_resolver: ForEachItemsResolving,
        included_steps_resolver: IncludedWorkflowStepsResolving,
        runtime_rebaser: IncludeGroupRuntimeRebasing,
        context_resolver: WorkflowStepContextResolving,
        template_selector: IncludeGroupTemplatesSelecting,
        instance_collector: MaterializedWorkflowInstancesCollecting,
        dependency_rebaser: OwnedIncludeDependenciesRebasing,
    ) -> None:
        self._readiness_checker = readiness_checker
        self._items_resolver = items_resolver
        self._included_steps_resolver = included_steps_resolver
        self._runtime_rebaser = runtime_rebaser
        self._context_resolver = context_resolver
        self._template_selector = template_selector
        self._instance_collector = instance_collector
        self._dependency_rebaser = dependency_rebaser

    def materialize(
        self,
        group: IncludeAliasGroup,
        owner_group: IncludeAliasGroup | None,
        owner_instance: IncludedWorkflowInstance | None,
        all_groups: list[IncludeAliasGroup],
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> IncludeGroupTreeMaterialization:
        templates = self._template_selector.select(flow, group)
        runtime = (
            self._runtime_rebaser.rebase(
                group,
                templates,
                owner_group,
                owner_instance,
            )
            if owner_group is not None and owner_instance is not None
            else IncludeGroupRuntime(group=group, templates=templates)
        )
        if not self._readiness_checker.is_ready(runtime.group, run_state):
            return IncludeGroupTreeMaterialization(steps=[], groups=[])
        binding_context = (
            self._context_resolver.resolve(
                context,
                owner_instance,
                owner_instance.source_item,
            )
            if owner_instance is not None
            else context
        )
        items = (
            self._items_resolver.resolve(
                runtime.group.alias,
                runtime.group.for_each.source,
                context,
            )
            if runtime.group.for_each is not None
            else [None]
        )
        instance_steps = [
            self._included_steps_resolver.resolve(
                runtime.group,
                runtime.templates,
                iteration_index,
                item,
                binding_context,
            )
            for iteration_index, item in enumerate(items)
        ]
        steps = [
            instance[template_index]
            for template_index in range(len(runtime.templates))
            for instance in instance_steps
            if template_index < len(instance)
        ]
        child_groups = [
            child_group
            for child_group in all_groups
            if child_group.owner_alias == group.alias
        ]
        child_aliases = [child_group.alias for child_group in child_groups]
        steps = [
            replace(
                step,
                depends_on=self._dependency_rebaser.rebase(
                    step.depends_on,
                    child_aliases,
                    group,
                    step.workflow_instance,
                ),
            )
            if step.workflow_instance is not None
            else step
            for step in steps
        ]
        nested_results = [
            self.materialize(
                group=child_group,
                owner_group=group,
                owner_instance=instance,
                all_groups=all_groups,
                flow=flow,
                run_state=run_state,
                context=context,
            )
            for child_group in child_groups
            for instance in self._instance_collector.collect(steps)
        ]
        return IncludeGroupTreeMaterialization(
            steps=[
                *steps,
                *[
                    nested_step
                    for result in nested_results
                    for nested_step in result.steps
                ],
            ],
            groups=[
                replace(runtime.group, member_ids=[step.id for step in steps]),
                *[
                    nested_group
                    for result in nested_results
                    for nested_group in result.groups
                ],
            ],
        )

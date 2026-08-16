"""Resolves dynamic workflow includes into executable child steps."""

from __future__ import annotations

from harness.dynamic_workflow_steps_resolving import DynamicWorkflowStepsResolving
from harness.for_each_items_resolving import ForEachItemsResolving
from harness.include_group_dynamic_checking import IncludeGroupDynamicChecking
from harness.include_group_readiness_checking import IncludeGroupReadinessChecking
from harness.included_workflow_steps_resolving import IncludedWorkflowStepsResolving
from harness.models import FlowDef, RunState, StepDef
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: DynamicWorkflowStepsResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves ready dynamic workflow groups alongside ordinary executable steps.
"""
class DynamicWorkflowStepsResolver(DynamicWorkflowStepsResolving):

    def __init__(
        self,
        dynamic_checker: IncludeGroupDynamicChecking,
        readiness_checker: IncludeGroupReadinessChecking,
        items_resolver: ForEachItemsResolving,
        included_steps_resolver: IncludedWorkflowStepsResolving,
    ) -> None:
        self._dynamic_checker = dynamic_checker
        self._readiness_checker = readiness_checker
        self._items_resolver = items_resolver
        self._included_steps_resolver = included_steps_resolver

    def resolve(
        self,
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> list[StepDef]:
        dynamic_groups = [
            group
            for group in flow.alias_groups
            if self._dynamic_checker.is_dynamic(group)
        ]
        dynamic_member_ids = {
            member_id
            for group in dynamic_groups
            for member_id in group.member_ids
        }
        resolved_steps = [
            step for step in flow.steps if step.id not in dynamic_member_ids
        ]
        for group in dynamic_groups:
            if not self._readiness_checker.is_ready(group, run_state):
                continue
            templates = [
                step for step in flow.steps if step.id in group.member_ids
            ]
            items = (
                self._items_resolver.resolve(
                    group.alias,
                    group.for_each,
                    context,
                )
                if group.for_each is not None
                else [None]
            )
            for iteration_index, item in enumerate(items):
                resolved_steps.extend(
                    self._included_steps_resolver.resolve(
                        group,
                        templates,
                        iteration_index,
                        item,
                        context,
                    )
                )
        return resolved_steps

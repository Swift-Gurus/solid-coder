"""Resolves dynamic workflow includes into executable child steps."""

from __future__ import annotations

from harness.dynamic_workflow_materialization import DynamicWorkflowMaterialization
from harness.dynamic_workflow_steps_resolving import DynamicWorkflowStepsResolving
from harness.dynamic_workflow_materializing import DynamicWorkflowMaterializing
from harness.group_dependency_expanding import GroupDependencyExpanding
from harness.models import FlowDef, RunState
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
        materializer: DynamicWorkflowMaterializing,
        group_dependency_expander: GroupDependencyExpanding,
    ) -> None:
        self._materializer = materializer
        self._group_dependency_expander = group_dependency_expander

    def resolve(
        self,
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> DynamicWorkflowMaterialization:
        materialization = self._materializer.materialize(
            flow,
            run_state,
            context,
        )
        resolved_steps = [
            step
            for step in flow.steps
            if step.id not in materialization.authored_member_ids
        ]
        resolved_steps.extend(materialization.steps)
        return DynamicWorkflowMaterialization(
            steps=self._group_dependency_expander.expand(
                resolved_steps,
                materialization.groups,
            ),
            groups=[
                group
                for group in flow.alias_groups
                if group.alias not in materialization.authored_group_aliases
            ] + materialization.groups,
            authored_group_aliases=materialization.authored_group_aliases,
            authored_member_ids=materialization.authored_member_ids,
        )

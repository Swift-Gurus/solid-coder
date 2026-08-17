"""Resolves dependency identities for an included workflow step."""

from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_dependencies_resolving import (
    IncludedWorkflowDependenciesResolving,
)
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.models import StepDef


"""
solid-name: IncludedWorkflowDependenciesResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves child-step dependencies within one included workflow runtime instance.
"""
class IncludedWorkflowDependenciesResolver(IncludedWorkflowDependenciesResolving):
    def resolve(
        self,
        template: StepDef,
        group: IncludeAliasGroup,
        step_identities: IncludedWorkflowStepIdentities,
    ) -> list[str]:
        member_ids = group.member_ids
        resolved = [
            step_identities.require_declaration(dependency).execution_step_id
            if step_identities.contains_declaration(dependency)
            else dependency
            for dependency in template.depends_on
        ]
        has_internal_dependency = any(
            dependency in member_ids
            for dependency in template.depends_on
        )
        return resolved if has_internal_dependency else [*group.depends_on, *resolved]

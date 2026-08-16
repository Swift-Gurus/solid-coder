"""Resolves dependency identities for an included workflow step."""

from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_dependencies_resolving import (
    IncludedWorkflowDependenciesResolving,
)
from harness.included_workflow_identifier_qualifying import (
    IncludedWorkflowIdentifierQualifying,
)
from harness.models import StepDef


"""
solid-name: IncludedWorkflowDependenciesResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves child-step dependencies within one included workflow runtime instance.
"""
class IncludedWorkflowDependenciesResolver(IncludedWorkflowDependenciesResolving):

    def __init__(
        self,
        identifier_qualifier: IncludedWorkflowIdentifierQualifying,
    ) -> None:
        self._identifier_qualifier = identifier_qualifier

    def resolve(
        self,
        template: StepDef,
        group: IncludeAliasGroup,
        instance_prefix: str,
    ) -> list[str]:
        member_ids = set(group.member_ids)
        resolved = [
            self._identifier_qualifier.qualify(
                dependency,
                group.alias,
                instance_prefix,
            )
            if dependency in member_ids
            else dependency
            for dependency in template.depends_on
        ]
        has_internal_dependency = any(
            dependency in member_ids for dependency in template.depends_on
        )
        return resolved if has_internal_dependency else [*group.depends_on, *resolved]

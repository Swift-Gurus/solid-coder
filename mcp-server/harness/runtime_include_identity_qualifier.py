"""Qualifies nested declarations beneath one included workflow instance."""

from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.included_workflow_step_identity_resolving import (
    IncludedWorkflowStepIdentityResolving,
)
from harness.runtime_include_identity_qualifying import (
    RuntimeIncludeIdentityQualifying,
)


"""
solid-name: RuntimeIncludeIdentityQualifier
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Qualifies nested runtime declaration identities beneath one materialized workflow instance.
"""
class RuntimeIncludeIdentityQualifier(RuntimeIncludeIdentityQualifying):
    def __init__(
        self,
        identity_resolver: IncludedWorkflowStepIdentityResolving,
    ) -> None:
        self._identity_resolver = identity_resolver

    def qualify(
        self,
        declaration_id: str,
        owner_group: IncludeAliasGroup,
        owner_instance: IncludedWorkflowInstance,
    ) -> str:
        return self._identity_resolver.resolve(
            declaration_id,
            owner_group.alias,
            owner_instance.instance_id,
        ).execution_step_id

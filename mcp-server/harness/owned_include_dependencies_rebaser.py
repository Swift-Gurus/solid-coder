"""Rebases dependencies owned by one materialized include instance."""

from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.owned_include_dependencies_rebasing import (
    OwnedIncludeDependenciesRebasing,
)
from harness.runtime_include_identity_qualifying import (
    RuntimeIncludeIdentityQualifying,
)


"""
solid-name: OwnedIncludeDependenciesRebaser
solid-category: service
solid-spec: [SPEC-037]
solid-description: Qualifies child-group dependencies for the parent workflow instance that owns each materialized step.
"""
class OwnedIncludeDependenciesRebaser(OwnedIncludeDependenciesRebasing):
    def __init__(
        self,
        identity: RuntimeIncludeIdentityQualifying,
    ) -> None:
        self._identity = identity

    def rebase(
        self,
        dependencies: list[str],
        scoped_ids: list[str],
        owner_group: IncludeAliasGroup,
        owner_instance: IncludedWorkflowInstance,
    ) -> list[str]:
        return [
            self._identity.qualify(
                dependency,
                owner_group,
                owner_instance,
            )
            if dependency in scoped_ids
            else dependency
            for dependency in dependencies
        ]

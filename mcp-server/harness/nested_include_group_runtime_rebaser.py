"""Rebases nested include declarations beneath one parent runtime instance."""

from dataclasses import replace

from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_runtime import IncludeGroupRuntime
from harness.include_group_runtime_rebasing import IncludeGroupRuntimeRebasing
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import StepDef
from harness.owned_include_dependencies_rebasing import (
    OwnedIncludeDependenciesRebasing,
)
from harness.runtime_include_identity_qualifying import (
    RuntimeIncludeIdentityQualifying,
)


"""
solid-name: NestedIncludeGroupRuntimeRebaser
solid-category: service
solid-spec: [SPEC-037]
solid-description: Rebuilds a nested include group and its templates for one exact materialized parent instance.
"""
class NestedIncludeGroupRuntimeRebaser(IncludeGroupRuntimeRebasing):
    def __init__(
        self,
        identity: RuntimeIncludeIdentityQualifying,
        dependency_rebaser: OwnedIncludeDependenciesRebasing,
    ) -> None:
        self._identity = identity
        self._dependency_rebaser = dependency_rebaser

    def rebase(
        self,
        group: IncludeAliasGroup,
        templates: list[StepDef],
        owner_group: IncludeAliasGroup,
        owner_instance: IncludedWorkflowInstance,
    ) -> IncludeGroupRuntime:
        scoped_ids = [*owner_group.member_ids, *group.member_ids]
        runtime_group = replace(
            group,
            alias=self._identity.qualify(
                group.alias,
                owner_group,
                owner_instance,
            ),
            owner_alias=None,
            runtime_owner_instance_id=owner_instance.instance_id,
            member_ids=[
                self._identity.qualify(member_id, owner_group, owner_instance)
                for member_id in group.member_ids
            ],
            depends_on=self._dependency_rebaser.rebase(
                group.depends_on,
                scoped_ids,
                owner_group,
                owner_instance,
            ),
            for_each=(
                replace(
                    group.for_each,
                    source=replace(
                        group.for_each.source,
                        step_id=self._identity.qualify(
                            group.for_each.source.step_id,
                            owner_group,
                            owner_instance,
                        ),
                    ),
                )
                if group.for_each is not None
                and group.for_each.source.step_id in scoped_ids
                else group.for_each
            ),
        )
        return IncludeGroupRuntime(
            group=runtime_group,
            templates=[
                replace(
                    template,
                    id=self._identity.qualify(
                        template.id,
                        owner_group,
                        owner_instance,
                    ),
                    depends_on=self._dependency_rebaser.rebase(
                        template.depends_on,
                        scoped_ids,
                        owner_group,
                        owner_instance,
                    ),
                )
                for template in templates
            ],
        )

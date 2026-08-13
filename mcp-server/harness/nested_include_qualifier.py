"""Qualifies nested include resolutions under an owning alias."""

from dataclasses import replace

from harness.include_alias_group_creating import IncludeAliasGroupCreating
from harness.include_resolution import IncludeResolution
from harness.nested_include_qualifying import NestedIncludeQualifying
from harness.step_qualifying import StepQualifying


"""
solid-name: NestedIncludeQualifier
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Qualifies nested workflow steps and groups under their owning alias.
"""
class NestedIncludeQualifier(NestedIncludeQualifying):

    def __init__(
        self,
        step_qualifier: StepQualifying,
        alias_group_factory: IncludeAliasGroupCreating,
    ) -> None:
        self._step_qualifier = step_qualifier
        self._alias_group_factory = alias_group_factory

    def qualify(self, alias: str, nested: IncludeResolution) -> IncludeResolution:
        local_dependency_ids = {
            step["id"] for step in nested.steps
        } | {group.alias for group in nested.alias_groups}
        qualified_steps = [
            self._step_qualifier.qualify(step, alias, local_dependency_ids)
            for step in nested.steps
        ]
        qualified_groups = [
            self._alias_group_factory.create(
                alias=f"{alias}.{group.alias}",
                member_ids=[f"{alias}.{member}" for member in group.member_ids],
            )
            for group in nested.alias_groups
        ]
        return replace(
            nested,
            steps=qualified_steps,
            alias_groups=qualified_groups,
        )

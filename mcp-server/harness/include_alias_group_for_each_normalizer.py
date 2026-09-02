"""Normalizes one include group's typed iteration source."""

from dataclasses import replace

from harness.for_each_source_identity_resolving import (
    ForEachSourceIdentityResolving,
)
from harness.for_each_source_identity_scope import ForEachSourceIdentityScope
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_for_each_normalizing import (
    IncludeAliasGroupForEachNormalizing,
)


"""
solid-name: IncludeAliasGroupForEachNormalizer
solid-category: service
solid-spec: [SPEC-035, SPEC-037]
solid-description: Normalizes an include group's typed iteration-source identity.
"""
class IncludeAliasGroupForEachNormalizer(
    IncludeAliasGroupForEachNormalizing
):
    def __init__(
        self,
        source_identity: ForEachSourceIdentityResolving,
    ) -> None:
        self._source_identity = source_identity

    def normalize(
        self,
        group: IncludeAliasGroup,
        all_groups: list[IncludeAliasGroup],
    ) -> IncludeAliasGroup:
        if group.for_each is None:
            return group
        return replace(
            group,
            for_each=replace(
                group.for_each,
                source=replace(
                    group.for_each.source,
                    step_id=self._source_identity.resolve(
                        group.for_each.source.step_id,
                        ForEachSourceIdentityScope(
                            member_ids=group.member_ids,
                            excluded_aliases=[group.alias],
                        ),
                        all_groups,
                    ),
                ),
            ),
        )

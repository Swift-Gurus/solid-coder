"""Resolves assembled workflow iteration source identities."""

from harness.for_each_source_identity_resolving import (
    ForEachSourceIdentityResolving,
)
from harness.for_each_source_identity_scope import ForEachSourceIdentityScope
from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: ForEachSourceIdentityResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-037]
solid-description: Selects the narrowest owning include group and qualifies one child-local iteration source identity.
"""
class ForEachSourceIdentityResolver(ForEachSourceIdentityResolving):
    def resolve(
        self,
        local_source_id: str,
        scope: ForEachSourceIdentityScope,
        groups: list[IncludeAliasGroup],
    ) -> str:
        owners = [
            group
            for group in groups
            if group.alias not in scope.excluded_aliases
            and all(
                member_id in group.member_ids
                for member_id in scope.member_ids
            )
        ]
        if not owners:
            return local_source_id
        owner = min(owners, key=lambda group: len(group.member_ids))
        return f"{owner.alias}.{local_source_id}"

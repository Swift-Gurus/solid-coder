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
        if any(
            local_source_id in group.member_ids
            for group in groups
        ):
            return local_source_id
        target_group = next(
            (
                group
                for group in groups
                if group.alias in scope.excluded_aliases
            ),
            None,
        )
        if target_group is not None:
            for group in groups:
                candidate = f"{group.alias}.{local_source_id}"
                if (
                    candidate in target_group.depends_on
                    and candidate in group.member_ids
                ):
                    return candidate
        if target_group is not None and target_group.owner_alias is not None:
            owner_group = next(
                (
                    group
                    for group in groups
                    if group.alias == target_group.owner_alias
                ),
                None,
            )
            owned_source_id = f"{target_group.owner_alias}.{local_source_id}"
            if (
                owner_group is not None
                and owned_source_id in owner_group.member_ids
            ):
                return owned_source_id
        owners = [
            group
            for group in groups
            if group.alias not in scope.excluded_aliases
            and f"{group.alias}.{local_source_id}" in group.member_ids
            and all(
                member_id in group.member_ids
                for member_id in scope.member_ids
            )
        ]
        if not owners:
            return local_source_id
        owner = min(owners, key=lambda group: len(group.member_ids))
        return f"{owner.alias}.{local_source_id}"

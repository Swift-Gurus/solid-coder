"""Defines resolution of an assembled workflow iteration source identity."""

from typing import Protocol

from harness.for_each_source_identity_scope import ForEachSourceIdentityScope
from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: ForEachSourceIdentityResolving
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for resolving one local iteration source through explicit include membership.
"""
class ForEachSourceIdentityResolving(Protocol):
    def resolve(
        self,
        local_source_id: str,
        scope: ForEachSourceIdentityScope,
        groups: list[IncludeAliasGroup],
    ) -> str: ...

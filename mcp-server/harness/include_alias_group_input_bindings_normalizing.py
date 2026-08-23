"""Defines normalization of include-group input bindings."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeAliasGroupInputBindingsNormalizing
solid-category: abstraction
solid-spec: [SPEC-035, SPEC-037]
solid-description: Contract for normalizing typed step-output references carried by include-group input bindings.
"""
class IncludeAliasGroupInputBindingsNormalizing(Protocol):
    def normalize(
        self,
        group: IncludeAliasGroup,
        all_groups: list[IncludeAliasGroup],
    ) -> IncludeAliasGroup: ...

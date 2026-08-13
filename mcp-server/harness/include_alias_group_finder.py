"""Finds include-alias groups by name."""

from __future__ import annotations

from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_finding import IncludeAliasGroupFinding


"""
solid-name: IncludeAliasGroupFinder
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Finds a workflow include-alias group by its alias.
"""
class IncludeAliasGroupFinder(IncludeAliasGroupFinding):

    def find(
        self,
        alias: str,
        groups: list[IncludeAliasGroup],
    ) -> IncludeAliasGroup | None:
        return next((group for group in groups if group.alias == alias), None)

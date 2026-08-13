"""Defines lookup of include-alias groups by name."""

from __future__ import annotations

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeAliasGroupFinding
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for finding a workflow include-alias group by its alias.
"""
class IncludeAliasGroupFinding(Protocol):

    def find(
        self,
        alias: str,
        groups: list[IncludeAliasGroup],
    ) -> IncludeAliasGroup | None: ...

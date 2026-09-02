"""Carries dynamic include groups and their executable roots."""

from dataclasses import dataclass

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: DynamicIncludeGroupHierarchy
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries all dynamic include groups and the roots whose owners are outside the dynamic hierarchy.
"""
@dataclass(frozen=True)
class DynamicIncludeGroupHierarchy:
    groups: list[IncludeAliasGroup]
    roots: list[IncludeAliasGroup]

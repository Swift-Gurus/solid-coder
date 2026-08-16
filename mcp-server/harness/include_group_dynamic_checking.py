"""Defines classification of a workflow include group as dynamic."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeGroupDynamicChecking
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for identifying include groups that require runtime materialization.
"""
class IncludeGroupDynamicChecking(Protocol):
    def is_dynamic(self, group: IncludeAliasGroup) -> bool: ...

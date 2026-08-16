"""Defines restoration of one include alias group entry."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeAliasGroupEntryParsing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for restoring one include group from a workflow snapshot entry.
"""
class IncludeAliasGroupEntryParsing(Protocol):
    def parse(self, raw: object) -> IncludeAliasGroup: ...

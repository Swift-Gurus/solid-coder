"""Defines restoration of include groups from a workflow snapshot."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeAliasGroupSnapshotParsing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for restoring typed include groups from durable workflow snapshots.
"""
class IncludeAliasGroupSnapshotParsing(Protocol):
    def parse(self, raw: object) -> list[IncludeAliasGroup]: ...

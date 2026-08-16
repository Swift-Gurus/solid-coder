"""Restores include groups from a durable workflow snapshot."""

from harness.flow_validation_error import FlowValidationError
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_entry_parsing import IncludeAliasGroupEntryParsing
from harness.include_alias_group_snapshot_parsing import (
    IncludeAliasGroupSnapshotParsing,
)


"""
solid-name: IncludeAliasGroupSnapshotParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Restores validated include-group collections from workflow snapshots.
"""
class IncludeAliasGroupSnapshotParser(IncludeAliasGroupSnapshotParsing):

    def __init__(self, group_parser: IncludeAliasGroupEntryParsing) -> None:
        self._group_parser = group_parser

    def parse(self, raw: object) -> list[IncludeAliasGroup]:
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise FlowValidationError("Workflow snapshot alias_groups must be an array")
        return [self._group_parser.parse(entry) for entry in raw]

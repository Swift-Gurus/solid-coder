"""Recognizes path-based workflow include entries."""

from __future__ import annotations

from collections.abc import Mapping

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.path_include_entry import PathIncludeEntry
from harness.path_include_entry_reading import PathIncludeEntryReading


"""
solid-name: PathIncludeEntryReader
solid-category: boundary
solid-spec: [SPEC-027, SPEC-045]
solid-description: Validates raw path-include fields and maps them into a typed include entry.
"""
class PathIncludeEntryReader(PathIncludeEntryReading):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def read(self, raw: Mapping[str, object]) -> PathIncludeEntry | None:
        path = raw.get("include")
        if not isinstance(path, str):
            return None
        alias = raw.get("as")
        if not isinstance(alias, str) or not alias:
            raise self._error_factory.create(
                "Path workflow include must declare a non-empty 'as' alias"
            )
        source_file = raw.get("__source_file")
        if source_file is not None and not isinstance(source_file, str):
            raise self._error_factory.create(
                f"Path workflow include '{alias}' has an invalid declaring source"
            )
        return PathIncludeEntry(
            path=path,
            alias=alias,
            source_file=source_file,
        )

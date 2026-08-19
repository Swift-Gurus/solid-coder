"""Restores optional for-each references from alias-group snapshots."""

from __future__ import annotations

from harness.for_each_reference_parsing import ForEachReferenceParsing
from harness.include_alias_group_for_each_parsing import (
    IncludeAliasGroupForEachParsing,
)
from harness.step_output_reference import StepOutputReference


"""
solid-name: IncludeAliasGroupForEachParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Restores an optional workflow iteration reference for an include alias group when a reference is present.
"""
class IncludeAliasGroupForEachParser(IncludeAliasGroupForEachParsing):
    def __init__(self, reference_parser: ForEachReferenceParsing) -> None:
        self._reference_parser = reference_parser

    def parse(
        self,
        alias: str,
        raw: object,
    ) -> StepOutputReference | None:
        if raw is None:
            return None
        return self._reference_parser.parse(alias, raw)

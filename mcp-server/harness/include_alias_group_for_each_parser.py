"""Restores optional for-each references from alias-group snapshots."""

from __future__ import annotations

from harness.for_each_declaration import ForEachDeclaration
from harness.for_each_declaration_parsing import ForEachDeclarationParsing
from harness.include_alias_group_for_each_parsing import (
    IncludeAliasGroupForEachParsing,
)


"""
solid-name: IncludeAliasGroupForEachParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Restores an optional workflow iteration reference for an include alias group when a reference is present.
"""
class IncludeAliasGroupForEachParser(IncludeAliasGroupForEachParsing):
    def __init__(self, declaration_parser: ForEachDeclarationParsing) -> None:
        self._declaration_parser = declaration_parser

    def parse(
        self,
        alias: str,
        raw: object,
    ) -> ForEachDeclaration | None:
        if raw is None:
            return None
        return self._declaration_parser.parse(alias, raw)

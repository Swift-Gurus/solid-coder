"""Converts individual Swift parser items into typed source units."""

from typing import Optional

from source.source_line_range import SourceLineRange
from source.source_offset_line_resolving import SourceOffsetLineResolving
from source.source_unit import SourceUnit
from source.swift_ast_item_decoding import SwiftASTItemDecoding
from source.swift_ast_unit_kind_resolving import SwiftASTUnitKindResolving
from source.swift_ast_unit_name_resolving import SwiftASTUnitNameResolving


"""
solid-name: SwiftASTItemDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Converts supported Swift declaration items into source-unit metadata with stable identities and spans.
"""
class SwiftASTItemDecoder(SwiftASTItemDecoding):
    def __init__(
        self,
        kind_resolver: SwiftASTUnitKindResolving,
        name_resolver: SwiftASTUnitNameResolving,
        line_resolver: SourceOffsetLineResolving,
    ) -> None:
        self._kind_resolver = kind_resolver
        self._name_resolver = name_resolver
        self._line_resolver = line_resolver

    def decode(self, item: object, source: str) -> Optional[SourceUnit]:
        if not isinstance(item, dict):
            return None
        kind = self._kind_resolver.resolve(
            item.get("_kind"),
            item.get("actor"),
        )
        name = self._name_resolver.resolve(
            kind,
            item.get("name"),
            item.get("extended_type"),
        )
        source_range = item.get("range")
        if kind is None or not name or not isinstance(source_range, dict):
            return None
        start_offset = source_range.get("start")
        end_offset = source_range.get("end")
        if not isinstance(start_offset, int) or not isinstance(end_offset, int):
            return None
        start_line = self._line_resolver.resolve(source, start_offset)
        end_line = self._line_resolver.resolve(source, end_offset)
        return SourceUnit(
            identity=f"{kind.value}:{name}:{start_line}",
            kind=kind,
            name=name,
            span=SourceLineRange(start=start_line, end=end_line),
            start_offset=start_offset,
            end_offset=end_offset,
        )

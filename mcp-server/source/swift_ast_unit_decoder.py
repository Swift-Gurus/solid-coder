"""Decodes Swift parser output into typed source units."""

from source.source_unit import SourceUnit
from source.swift_ast_item_decoding import SwiftASTItemDecoding
from source.swift_ast_items_loading import SwiftASTItemsLoading
from source.swift_ast_unit_decoding import SwiftASTUnitDecoding


"""
solid-name: SwiftASTUnitDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Converts parser output into ordered source-unit metadata with stable identities and spans.
"""
class SwiftASTUnitDecoder(SwiftASTUnitDecoding):
    def __init__(
        self,
        items_loader: SwiftASTItemsLoading,
        item_decoder: SwiftASTItemDecoding,
    ) -> None:
        self._items_loader = items_loader
        self._item_decoder = item_decoder

    def decode(self, parser_json: str, source: str) -> list[SourceUnit]:
        units: list[SourceUnit] = []
        for item in self._items_loader.load(parser_json):
            unit = self._item_decoder.decode(item, source)
            if unit is not None:
                units.append(unit)
        return units

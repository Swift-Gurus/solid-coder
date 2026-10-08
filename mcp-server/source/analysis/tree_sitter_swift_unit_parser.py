"""Adapts Swift declarations to typed source units."""

from tree_sitter import Node

from findings.review_unit_kind import ReviewUnitKind
from findings.review_unit_kind_parsing import ReviewUnitKindParsing
from source.analysis.swift_member_decoder import SwiftMembersDecoding
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_line_range import SourceLineRange
from source.source_unit import SourceUnit, SourceUnitSignature


"""
solid-name: TreeSitterSwiftUnitParser
solid-category: boundary-adapter
solid-spec: [SPEC-057, SPEC-062]
solid-description: Produces typed Swift declaration inventories with direct members, declaration headers, and source locations.
"""
class TreeSitterSwiftUnitParser(SourceSyntaxParsing[Node, SourceUnit | None]):
    def __init__(
        self,
        unit_kinds: ReviewUnitKindParsing,
        spans: SourceSyntaxParsing[Node, SourceLineRange],
        members: SwiftMembersDecoding,
        signatures: SourceSyntaxParsing[Node, SourceUnitSignature],
    ) -> None:
        self._unit_kinds = unit_kinds
        self._spans = spans
        self._members = members
        self._signatures = signatures

    def parse(self, source: Node) -> SourceUnit | None:
        declaration_kind = source.child_by_field_name("declaration_kind")
        kind = ReviewUnitKind.FUNCTION if source.type == "function_declaration" else None
        if declaration_kind is not None and declaration_kind.text:
            kind = self._unit_kinds.parse(declaration_kind.text.decode("utf-8"))
        name = source.child_by_field_name("name")
        if kind is None or name is None or not name.text or name.is_missing:
            return None
        unit_name = name.text.decode("utf-8")
        span = self._spans.parse(source)
        identity = f"{kind.value}:{unit_name}:{span.start}"
        return SourceUnit(
            identity=identity,
            kind=kind,
            name=unit_name,
            span=span,
            start_offset=source.start_byte,
            end_offset=max(source.start_byte, source.end_byte - 1),
            members=self._members.decode(source, kind, identity),
            signature=self._signatures.parse(source),
        )

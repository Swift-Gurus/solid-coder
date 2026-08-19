"""Normalizes Swift parser declaration kinds."""

from typing import Optional

from findings.review_unit_kind import ReviewUnitKind
from findings.review_unit_kind_parsing import ReviewUnitKindParsing
from source.swift_ast_unit_kind_resolving import SwiftASTUnitKindResolving


"""
solid-name: SwiftASTUnitKindResolver
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Resolves Swift declaration identities into the shared source-unit kind vocabulary.
"""
class SwiftASTUnitKindResolver(SwiftASTUnitKindResolving):
    def __init__(self, parser: ReviewUnitKindParsing) -> None:
        self._parser = parser

    def resolve(
        self,
        raw_kind: object,
        actor_marker: object,
    ) -> Optional[ReviewUnitKind]:
        if raw_kind == "class_decl" and actor_marker is True:
            return ReviewUnitKind.ACTOR
        if raw_kind == "func_decl":
            return ReviewUnitKind.FUNCTION
        if raw_kind == "protocol":
            return ReviewUnitKind.PROTOCOL
        if not isinstance(raw_kind, str):
            return None
        return self._parser.parse(raw_kind.removesuffix("_decl"))

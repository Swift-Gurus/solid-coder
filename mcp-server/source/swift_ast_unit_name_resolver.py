"""Normalizes Swift parser declaration names."""

from typing import Optional

from findings.review_unit_kind import ReviewUnitKind
from source.swift_ast_unit_name_resolving import SwiftASTUnitNameResolving


"""
solid-name: SwiftASTUnitNameResolver
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Resolves source-unit names from external Swift declaration name representations.
"""
class SwiftASTUnitNameResolver(SwiftASTUnitNameResolving):
    def resolve(
        self,
        kind: Optional[ReviewUnitKind],
        raw_name: object,
        extended_type: object,
    ) -> Optional[str]:
        if kind is ReviewUnitKind.EXTENSION:
            return extended_type if isinstance(extended_type, str) else None
        if not isinstance(raw_name, dict):
            return None
        base_name = raw_name.get("base_name")
        if not isinstance(base_name, dict):
            return None
        value = base_name.get("name")
        return value if isinstance(value, str) else None

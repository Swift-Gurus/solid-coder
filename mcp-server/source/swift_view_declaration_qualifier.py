"""Qualifies structured Swift view declarations."""

from source.swift_ast_unit_name_resolving import SwiftASTUnitNameResolving


"""
solid-name: SwiftViewDeclarationQualifier
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Recognizes view declarations from structured Swift source.
"""
class SwiftViewDeclarationQualifier:

    def __init__(self, name_resolver: SwiftASTUnitNameResolving) -> None:
        self._name_resolver = name_resolver

    def qualifies(self, item: object) -> bool:
        if not isinstance(item, dict) or item.get("_kind") != "struct_decl":
            return False
        members = item.get("members")
        if not isinstance(members, list):
            return False
        return any(self._member_name(member) == "body" for member in members)

    def _member_name(self, member: object) -> str:
        if not isinstance(member, dict) or member.get("_kind") != "var_decl":
            return ""
        resolved = self._name_resolver.resolve(
            kind=None,
            raw_name=member.get("name"),
            extended_type=None,
        )
        return resolved or ""

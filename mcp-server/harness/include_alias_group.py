"""Defines a named group of expanded workflow-step identifiers."""

from dataclasses import dataclass


"""
solid-name: IncludeAliasGroup
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Represents one workflow include alias and its expanded member-step identifiers.
"""
@dataclass(frozen=True)
class IncludeAliasGroup:
    alias: str
    member_ids: list[str]

    def contains(self, step_id: str) -> bool:
        return step_id in self.member_ids

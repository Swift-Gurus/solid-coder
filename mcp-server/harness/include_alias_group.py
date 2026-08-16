"""Defines a named group of expanded workflow-step identifiers."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.condition_declaration import ConditionDeclaration
from harness.workflow_input_binding import WorkflowInputBinding


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
    depends_on: list[str] = field(default_factory=list)
    for_each: str | None = None
    input_bindings: list[WorkflowInputBinding] = field(default_factory=list)
    condition: ConditionDeclaration | None = None

    @property
    def id(self) -> str:
        return self.alias

    def contains(self, step_id: str) -> bool:
        return step_id in self.member_ids

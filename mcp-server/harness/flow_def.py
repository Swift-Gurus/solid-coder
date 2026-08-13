"""Defines one resolved workflow definition."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.include_alias_group import IncludeAliasGroup
from harness.step_declaration import StepDeclaration
from harness.step_def import StepDef


"""
solid-name: FlowDef
solid-category: model
solid-spec: [SPEC-030, SPEC-035]
solid-description: Represents a resolved workflow definition.
"""
@dataclass(frozen=True)
class FlowDef:
    name: str
    max_turns: int
    steps: list[StepDef]
    id: str = ""
    source_path: str = ""
    sources: list[str] = field(default_factory=list)
    workflow_ids: list[str] = field(default_factory=list)
    step_declarations: list[StepDeclaration] = field(default_factory=list)
    top_level_step_ids: set[str] = field(default_factory=set)
    alias_groups: list[IncludeAliasGroup] = field(default_factory=list)
    include_chain: list[str] = field(default_factory=list)

    @property
    def workflow_id(self) -> str:
        return self.id or self.name

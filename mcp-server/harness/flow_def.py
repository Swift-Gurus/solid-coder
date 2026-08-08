"""Defines one resolved workflow definition."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.step_def import StepDef


"""
solid-name: FlowDef
solid-category: model
solid-spec: [SPEC-030, SPEC-035]
solid-description: Represents a resolved workflow with stable identity, source provenance, steps, and execution limit.
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
    raw_steps: list[dict] = field(default_factory=list)
    top_level_step_ids: set[str] = field(default_factory=set)
    alias_groups: dict[str, list[str]] = field(default_factory=dict)
    include_chain: list[str] = field(default_factory=list)

    @property
    def workflow_id(self) -> str:
        return self.id or self.name

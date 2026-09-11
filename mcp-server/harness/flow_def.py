"""Defines one resolved workflow definition."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.condition_declaration import ConditionDeclaration
from harness.include_alias_group import IncludeAliasGroup
from harness.rule_declaration import RuleDeclaration
from harness.step_declaration import StepDeclaration
from harness.step_def import StepDef
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: FlowDef
solid-category: model
solid-spec: [SPEC-030, SPEC-035, SPEC-037, SPEC-039]
solid-description: Represents a resolved workflow definition.
"""
@dataclass(frozen=True)
class FlowDef:
    name: str
    max_turns: int
    steps: list[StepDef]
    condition: ConditionDeclaration | None = None
    execution: WorkflowExecutionMode = WorkflowExecutionMode.GRANULAR
    presentation: WorkflowPresentationMode = WorkflowPresentationMode.INDIVIDUAL
    id: str = ""
    source_path: str = ""
    sources: list[str] = field(default_factory=list)
    workflow_ids: list[str] = field(default_factory=list)
    step_declarations: list[StepDeclaration] = field(default_factory=list)
    top_level_step_ids: set[str] = field(default_factory=set)
    alias_groups: list[IncludeAliasGroup] = field(default_factory=list)
    include_chain: list[str] = field(default_factory=list)
    rule: RuleDeclaration | None = None

    @property
    def workflow_id(self) -> str:
        return self.id or self.name

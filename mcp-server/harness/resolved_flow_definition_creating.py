"""Defines construction of resolved workflow definitions."""

from typing import Protocol

from harness.flow_def import FlowDef
from harness.include_alias_group import IncludeAliasGroup
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedFlowDefinitionCreating
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-035]
solid-description: Contract for creating a resolved workflow definition with composition and source provenance.
"""
class ResolvedFlowDefinitionCreating(Protocol):
    def create(
        self,
        workflow_id: str,
        name: str,
        max_turns: int,
        step_declarations: list[StepDeclaration],
        top_level_step_ids: set[str],
        alias_groups: list[IncludeAliasGroup],
        include_chain: list[str],
        source_path: str,
        sources: list[str],
        workflow_ids: list[str],
    ) -> FlowDef: ...

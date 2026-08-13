"""Creates resolved workflow definitions."""

from harness.flow_def import FlowDef
from harness.include_alias_group import IncludeAliasGroup
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedFlowDefinitionFactory
solid-category: factory
solid-spec: [SPEC-030, SPEC-035]
solid-description: Creates resolved workflow definitions with composition and source provenance.
"""
class ResolvedFlowDefinitionFactory:
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
    ) -> FlowDef:
        return FlowDef(
            id=workflow_id,
            name=name,
            max_turns=max_turns,
            steps=[],
            step_declarations=step_declarations,
            top_level_step_ids=top_level_step_ids,
            alias_groups=alias_groups,
            include_chain=include_chain,
            source_path=source_path,
            sources=sources,
            workflow_ids=workflow_ids,
        )

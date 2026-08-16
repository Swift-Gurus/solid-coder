"""Assembles an executable workflow definition."""

from harness.flow_def import FlowDef
from harness.group_dependency_expanding import GroupDependencyExpanding
from harness.include_group_dynamic_checking import IncludeGroupDynamicChecking
from harness.step_building import StepBuilding


"""
solid-name: FlowDefinitionAssembler
solid-category: service
solid-spec: [SPEC-030, SPEC-035, SPEC-037]
solid-description: Expands opaque group dependencies and builds the immutable executable workflow model.
"""
class FlowDefinitionAssembler:

    def __init__(
        self,
        group_dependency_expander: GroupDependencyExpanding,
        dynamic_group_checker: IncludeGroupDynamicChecking,
        step_builder: StepBuilding,
    ) -> None:
        self._group_dependency_expander = group_dependency_expander
        self._dynamic_group_checker = dynamic_group_checker
        self._step_builder = step_builder

    def assemble(self, definition: FlowDef) -> FlowDef:
        expanded_steps = self._group_dependency_expander.expand(
            definition.step_declarations,
            definition.alias_groups,
        )
        return FlowDef(
            id=definition.id,
            name=definition.name,
            max_turns=definition.max_turns,
            condition=definition.condition,
            steps=[self._step_builder.build(step) for step in expanded_steps],
            alias_groups=[
                group
                for group in definition.alias_groups
                if self._dynamic_group_checker.is_dynamic(group)
            ],
            source_path=definition.source_path,
            sources=definition.sources,
            workflow_ids=definition.workflow_ids,
        )

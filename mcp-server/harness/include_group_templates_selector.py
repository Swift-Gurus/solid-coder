"""Selects authored step templates owned by one include group."""

from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_templates_selecting import IncludeGroupTemplatesSelecting
from harness.models import FlowDef, StepDef


"""
solid-name: IncludeGroupTemplatesSelector
solid-category: service
solid-spec: [SPEC-037]
solid-description: Selects workflow-step templates by typed include-group membership.
"""
class IncludeGroupTemplatesSelector(IncludeGroupTemplatesSelecting):
    def select(
        self,
        flow: FlowDef,
        group: IncludeAliasGroup,
    ) -> list[StepDef]:
        return [step for step in flow.steps if step.id in group.member_ids]

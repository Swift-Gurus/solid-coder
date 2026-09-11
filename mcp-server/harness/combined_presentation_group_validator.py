"""Validates groups opting into combined model presentation."""

from harness.combined_presentation_group_validating import (
    CombinedPresentationGroupValidating,
)
from harness.flow_validation_error import FlowValidationError
from harness.for_each_mode import ForEachMode
from harness.include_alias_group import IncludeAliasGroup
from harness.step_declaration import StepDeclaration
from harness.workflow_execution_mode import WorkflowExecutionMode


"""
solid-name: CombinedPresentationGroupValidator
solid-category: service
solid-spec: [SPEC-043]
solid-description: Validates that combined workflow groups contain compatible batched agent work.
"""
class CombinedPresentationGroupValidator(CombinedPresentationGroupValidating):
    def validate(
        self,
        steps: list[StepDeclaration],
        groups: list[IncludeAliasGroup],
    ) -> None:
        for group in groups:
            if group.combined_presentation is None:
                continue
            if group.execution is WorkflowExecutionMode.AGGREGATE:
                continue
            if group.for_each is None or group.for_each.mode is not ForEachMode.BATCH:
                raise FlowValidationError(
                    f"Combined presentation rule '{group.authored_alias}' must use "
                    "batch for_each"
                )
            members = [step for step in steps if step.id in group.member_ids]
            if len(members) != 1 or members[0].type != "agent":
                raise FlowValidationError(
                    f"Combined presentation rule '{group.authored_alias}' must "
                    "contain exactly one agent step"
                )

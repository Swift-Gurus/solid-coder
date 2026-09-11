"""Identifies workflow include groups requiring runtime materialization."""

from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_dynamic_checking import IncludeGroupDynamicChecking
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: IncludeGroupDynamicChecker
solid-category: service
solid-spec: [SPEC-037]
solid-description: Identifies workflow include groups with runtime controls.
"""
class IncludeGroupDynamicChecker(IncludeGroupDynamicChecking):
    def is_dynamic(self, group: IncludeAliasGroup) -> bool:
        return bool(
            group.depends_on
            or group.for_each is not None
            or group.input_bindings
            or group.condition is not None
            or group.rule_workflow is not None
            or group.outputs
            or group.execution is not WorkflowExecutionMode.GRANULAR
            or group.presentation is not WorkflowPresentationMode.INDIVIDUAL
        )

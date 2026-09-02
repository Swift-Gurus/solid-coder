"""Defines runtime rebasing for a nested dynamic include group."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_runtime import IncludeGroupRuntime
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import StepDef


"""
solid-name: IncludeGroupRuntimeRebasing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for rebasing a nested include declaration under one materialized parent workflow instance.
"""
class IncludeGroupRuntimeRebasing(Protocol):
    def rebase(
        self,
        group: IncludeAliasGroup,
        templates: list[StepDef],
        owner_group: IncludeAliasGroup,
        owner_instance: IncludedWorkflowInstance,
    ) -> IncludeGroupRuntime: ...

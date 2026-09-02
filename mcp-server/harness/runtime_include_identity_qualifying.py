"""Defines runtime identity qualification beneath an included workflow instance."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_instance import IncludedWorkflowInstance


"""
solid-name: RuntimeIncludeIdentityQualifying
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for mapping a nested declaration identity beneath an exact materialized owner instance.
"""
class RuntimeIncludeIdentityQualifying(Protocol):
    def qualify(
        self,
        declaration_id: str,
        owner_group: IncludeAliasGroup,
        owner_instance: IncludedWorkflowInstance,
    ) -> str: ...

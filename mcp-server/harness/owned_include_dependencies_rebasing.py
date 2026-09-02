"""Defines rebasing of parent-step dependencies on owned include groups."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_instance import IncludedWorkflowInstance


"""
solid-name: OwnedIncludeDependenciesRebasing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for rebasing authored child-group dependencies beneath each exact parent workflow instance.
"""
class OwnedIncludeDependenciesRebasing(Protocol):
    def rebase(
        self,
        dependencies: list[str],
        scoped_ids: list[str],
        owner_group: IncludeAliasGroup,
        owner_instance: IncludedWorkflowInstance,
    ) -> list[str]: ...

"""Defines dependency resolution for an included workflow step."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.models import StepDef


"""
solid-name: IncludedWorkflowDependenciesResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving one child step's instance-scoped dependencies.
"""
class IncludedWorkflowDependenciesResolving(Protocol):
    def resolve(
        self,
        template: StepDef,
        group: IncludeAliasGroup,
        instance_prefix: str,
    ) -> list[str]: ...

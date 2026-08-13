"""Defines workflow group-dependency expansion."""

from __future__ import annotations

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.step_declaration import StepDeclaration


"""
solid-name: GroupDependencyExpanding
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for expanding group-alias dependencies into member-step dependencies.
"""
class GroupDependencyExpanding(Protocol):

    def expand(
        self,
        steps: list[StepDeclaration],
        alias_groups: list[IncludeAliasGroup],
    ) -> list[StepDeclaration]: ...

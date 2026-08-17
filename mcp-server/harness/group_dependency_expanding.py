"""Defines workflow group-dependency expansion."""

from __future__ import annotations

from typing import Protocol, TypeVar

from harness.graph_step_field_reading import GraphStepFieldReading
from harness.include_alias_group import IncludeAliasGroup

DependencyEntry = TypeVar("DependencyEntry", bound=GraphStepFieldReading)


"""
solid-name: GroupDependencyExpanding
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for expanding group-alias dependencies into member-step dependencies.
"""
class GroupDependencyExpanding(Protocol):

    def expand(
        self,
        steps: list[DependencyEntry],
        alias_groups: list[IncludeAliasGroup],
    ) -> list[DependencyEntry]: ...

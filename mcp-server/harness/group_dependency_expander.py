"""Expands workflow group dependencies."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from harness.group_dependency_expanding import GroupDependencyExpanding
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_finding import IncludeAliasGroupFinding
from harness.step_declaration import StepDeclaration


"""
solid-name: GroupDependencyExpander
solid-category: service
solid-spec: [SPEC-027]
solid-description: Expands group aliases into explicit member-step dependency references.
"""
class GroupDependencyExpander(GroupDependencyExpanding):

    def __init__(self, alias_group_finder: IncludeAliasGroupFinding) -> None:
        self._alias_group_finder = alias_group_finder

    def expand(
        self,
        steps: list[StepDeclaration],
        alias_groups: list[IncludeAliasGroup],
    ) -> list[StepDeclaration]:
        expanded: list[StepDeclaration] = []
        for step in steps:
            deps = cast(list[str], step.depends_on or [])
            new_deps: list[str] = []
            for dep in deps:
                group = self._alias_group_finder.find(dep, alias_groups)
                new_deps.extend(group.member_ids if group is not None else [dep])
            if new_deps == deps:
                expanded.append(step)
            else:
                expanded.append(replace(step, depends_on=new_deps))
        return expanded

"""Defines the typed result of compact metric expansion."""

from dataclasses import dataclass

from harness.include_alias_group import IncludeAliasGroup
from harness.step_declaration import StepDeclaration


"""
solid-name: CoLocatedMetricNormalization
solid-category: model
solid-spec: [SPEC-058]
solid-description: Represents expanded workflow steps and their preserved root and include ownership.
"""
@dataclass(frozen=True)
class CoLocatedMetricNormalization:
    steps: list[StepDeclaration]
    alias_groups: list[IncludeAliasGroup]
    top_level_step_ids: set[str]

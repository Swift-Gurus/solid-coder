"""Carries steps and runtime groups from one expanded include-group tree."""

from dataclasses import dataclass

from harness.include_alias_group import IncludeAliasGroup
from harness.models import StepDef


"""
solid-name: IncludeGroupTreeMaterialization
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries materialized steps and runtime groups produced by one dynamic include-group tree.
"""
@dataclass(frozen=True)
class IncludeGroupTreeMaterialization:
    steps: list[StepDef]
    groups: list[IncludeAliasGroup]

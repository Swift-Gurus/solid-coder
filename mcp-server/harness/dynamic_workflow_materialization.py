"""Carries runtime workflow steps and include groups produced by materialization."""

from dataclasses import dataclass

from harness.include_alias_group import IncludeAliasGroup
from harness.models import StepDef


"""
solid-name: DynamicWorkflowMaterialization
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries materialized workflow steps, runtime groups, and authored member identities excluded from direct execution.
"""
@dataclass(frozen=True)
class DynamicWorkflowMaterialization:
    steps: list[StepDef]
    groups: list[IncludeAliasGroup]
    authored_group_aliases: set[str]
    authored_member_ids: set[str]

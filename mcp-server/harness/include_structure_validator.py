"""Validates workflow include structure."""

from __future__ import annotations

from harness.graph_step_field_reading import GraphStepFieldReading
from harness.include_alias_collision_validating import IncludeAliasCollisionValidating
from harness.include_alias_group import IncludeAliasGroup
from harness.include_cycle_validator import IncludeCycleValidator
from harness.include_group_opacity_validating import IncludeGroupOpacityValidating


"""
solid-name: IncludeStructureValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Validates workflow include aliases, group opacity, and include cycles.
"""
class IncludeStructureValidator:

    def __init__(
        self,
        alias_collision_validator: IncludeAliasCollisionValidating,
        group_opacity_validator: IncludeGroupOpacityValidating,
        include_cycle_validator: IncludeCycleValidator,
    ) -> None:
        self._alias_collision_validator = alias_collision_validator
        self._group_opacity_validator = group_opacity_validator
        self._include_cycle_validator = include_cycle_validator

    def validate_includes(
        self,
        steps: list[GraphStepFieldReading],
        alias_groups: list[IncludeAliasGroup],
        top_level_step_ids: set[str],
        include_chain: list[str],
    ) -> None:
        self._alias_collision_validator.validate(alias_groups, top_level_step_ids)
        self._group_opacity_validator.validate(steps, alias_groups)
        self._include_cycle_validator.validate(include_chain)

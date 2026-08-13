"""Defines validation of include-alias collisions."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeAliasCollisionValidating
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for rejecting include aliases that collide with workflow-step identifiers.
"""
class IncludeAliasCollisionValidating(Protocol):

    def validate(
        self,
        alias_groups: list[IncludeAliasGroup],
        top_level_step_ids: set[str],
    ) -> None: ...

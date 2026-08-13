"""Validates include-alias collisions."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.include_alias_collision_validating import IncludeAliasCollisionValidating
from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeAliasCollisionValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Rejects include aliases that collide with workflow-step identifiers.
"""
class IncludeAliasCollisionValidator(IncludeAliasCollisionValidating):

    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(
        self,
        alias_groups: list[IncludeAliasGroup],
        top_level_step_ids: set[str],
    ) -> None:
        for group in alias_groups:
            if group.alias in top_level_step_ids:
                raise self._error_factory.create(
                    f"Include alias '{group.alias}' collides with an existing step ID"
                )

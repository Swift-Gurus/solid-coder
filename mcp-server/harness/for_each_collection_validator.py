"""Coordinates iteration-source validation across workflow entries."""

from __future__ import annotations

from harness.for_each_reference_validating import ForEachReferenceValidating
from harness.for_each_target_validating import ForEachTargetValidating
from harness.include_alias_group import IncludeAliasGroup
from harness.models import StepDef


"""
solid-name: ForEachCollectionValidator
solid-category: service
solid-spec: [SPEC-030, SPEC-037]
solid-description: Coordinates iteration-source validation for steps and included workflow groups.
"""
class ForEachCollectionValidator(ForEachReferenceValidating):

    def __init__(self, target_validator: ForEachTargetValidating) -> None:
        self._target_validator = target_validator

    def validate_for_each_references(
        self,
        steps: list[StepDef],
        alias_groups: list[IncludeAliasGroup] | None = None,
    ) -> None:
        for step in steps:
            self._target_validator.validate(
                target_id=step.id,
                for_each=step.for_each,
                dependency_ids=step.depends_on,
                steps=steps,
            )
        for group in alias_groups or []:
            self._target_validator.validate(
                target_id=group.alias,
                for_each=group.for_each,
                dependency_ids=group.depends_on,
                steps=steps,
            )

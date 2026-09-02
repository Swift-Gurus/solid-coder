"""Coordinates iteration-source validation across workflow entries."""

from __future__ import annotations

from harness.for_each_reference_validating import ForEachReferenceValidating
from harness.for_each_source_identity_resolving import (
    ForEachSourceIdentityResolving,
)
from harness.for_each_source_identity_scope import ForEachSourceIdentityScope
from harness.for_each_target_validating import ForEachTargetValidating
from harness.for_each_validation_target import ForEachValidationTarget
from harness.include_alias_group import IncludeAliasGroup
from harness.models import StepDef


"""
solid-name: ForEachCollectionValidator
solid-category: service
solid-spec: [SPEC-030, SPEC-037]
solid-description: Coordinates iteration-source validation for steps and included workflow groups.
"""
class ForEachCollectionValidator(ForEachReferenceValidating):

    def __init__(
        self,
        target_validator: ForEachTargetValidating,
        source_identity_resolver: ForEachSourceIdentityResolving,
    ) -> None:
        self._target_validator = target_validator
        self._source_identity_resolver = source_identity_resolver

    def validate_for_each_references(
        self,
        steps: list[StepDef],
        alias_groups: list[IncludeAliasGroup] | None = None,
    ) -> None:
        for step in steps:
            if step.for_each is None:
                continue
            self._target_validator.validate(
                target=ForEachValidationTarget(
                    target_id=step.id,
                    source_reference=step.for_each.source,
                    source_step_id=self._source_identity_resolver.resolve(
                        step.for_each.source.step_id,
                        ForEachSourceIdentityScope(member_ids=[step.id]),
                        alias_groups or [],
                    ),
                    dependency_ids=step.depends_on,
                ),
                steps=steps,
            )
        for group in alias_groups or []:
            if group.for_each is None:
                continue
            self._target_validator.validate(
                target=ForEachValidationTarget(
                    target_id=group.alias,
                    source_reference=group.for_each.source,
                    source_step_id=self._source_identity_resolver.resolve(
                        group.for_each.source.step_id,
                        ForEachSourceIdentityScope(
                            member_ids=group.member_ids,
                            excluded_aliases=[group.alias],
                        ),
                        alias_groups or [],
                    ),
                    dependency_ids=group.depends_on,
                ),
                steps=steps,
            )

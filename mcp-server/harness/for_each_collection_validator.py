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
from harness.workflow_output_collection_validating import (
    WorkflowOutputCollectionValidating,
)
from harness.workflow_output_collection_validation_target import (
    WorkflowOutputCollectionValidationTarget,
)
from harness.workflow_output_reference import WorkflowOutputReference

"""
solid-name: ForEachCollectionValidator
solid-category: service
solid-spec: [SPEC-030, SPEC-037, SPEC-056]
solid-description: Coordinates step-output iteration validation and workflow-output collection metric validation.
"""


class ForEachCollectionValidator(ForEachReferenceValidating):
    def __init__(
        self,
        target_validator: ForEachTargetValidating,
        workflow_output_validator: WorkflowOutputCollectionValidating,
        source_identity_resolver: ForEachSourceIdentityResolving,
    ) -> None:
        self._target_validator = target_validator
        self._workflow_output_validator = workflow_output_validator
        self._source_identity_resolver = source_identity_resolver

    def validate_for_each_references(
        self,
        steps: list[StepDef],
        alias_groups: list[IncludeAliasGroup] | None = None,
    ) -> None:
        for step in steps:
            if step.for_each is None:
                if step.metric_calculation is None:
                    continue
                source = step.metric_calculation.source
                item_condition = step.metric_calculation.condition
                metric_reducer = step.metric_calculation.reducer
                reference_name = "scoring.source"
                if isinstance(source, WorkflowOutputReference):
                    self._workflow_output_validator.validate(
                        target=WorkflowOutputCollectionValidationTarget(
                            target_id=step.id,
                            source_reference=source,
                            dependency_ids=step.depends_on,
                            item_condition=item_condition,
                            metric_reducer=metric_reducer,
                        ),
                        steps=steps,
                        alias_groups=alias_groups or [],
                    )
                    continue
            else:
                source = step.for_each.source
                item_condition = None
                metric_reducer = None
                reference_name = "for_each"
            self._target_validator.validate(
                target=ForEachValidationTarget(
                    target_id=step.id,
                    source_reference=source,
                    source_step_id=self._source_identity_resolver.resolve(
                        source.step_id,
                        ForEachSourceIdentityScope(member_ids=[step.id]),
                        alias_groups or [],
                    ),
                    dependency_ids=step.depends_on,
                    item_condition=item_condition,
                    metric_reducer=metric_reducer,
                    reference_name=reference_name,
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

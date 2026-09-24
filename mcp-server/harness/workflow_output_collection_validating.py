"""Defines validation of included workflow output collection sources."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.models import StepDef
from harness.workflow_output_collection_validation_target import (
    WorkflowOutputCollectionValidationTarget,
)


"""
solid-name: WorkflowOutputCollectionValidating
solid-category: abstraction
solid-spec: [SPEC-056]
solid-description: Validates projected child-workflow outputs used by collection-backed metrics.
"""
class WorkflowOutputCollectionValidating(Protocol):
    def validate(
        self,
        target: WorkflowOutputCollectionValidationTarget,
        steps: list[StepDef],
        alias_groups: list[IncludeAliasGroup],
    ) -> None: ...

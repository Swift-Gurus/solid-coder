"""Defines materialization of one included workflow instance."""

from __future__ import annotations

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.models import StepDef
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: IncludedWorkflowStepsResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for materializing one item-scoped included workflow DAG.
"""
class IncludedWorkflowStepsResolving(Protocol):
    def resolve(
        self,
        group: IncludeAliasGroup,
        templates: list[StepDef],
        iteration_index: int,
        item: object,
        context: WorkflowRunContext,
    ) -> list[StepDef]: ...

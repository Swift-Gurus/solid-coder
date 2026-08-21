"""Defines conditional policy application for one workflow-step instance."""

from __future__ import annotations

from typing import Protocol

from harness.condition_declaration import ConditionDeclaration
from harness.models import StepInstance
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: StepConditionApplying
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for applying a workflow condition decision to one expanded step instance.
"""
class StepConditionApplying(Protocol):
    def apply(
        self,
        instance: StepInstance,
        condition: ConditionDeclaration,
        item: object,
        context: WorkflowRunContext,
    ) -> StepInstance: ...

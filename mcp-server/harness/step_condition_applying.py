"""Defines conditional policy application for one workflow-step instance."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef, StepInstance
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
        step: StepDef,
        instance: StepInstance,
        context: WorkflowRunContext,
    ) -> StepInstance: ...

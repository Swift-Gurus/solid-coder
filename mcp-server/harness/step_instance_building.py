"""Defines materialization of one executable workflow step instance."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef, StepInstance
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: StepInstanceBuilding
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030, SPEC-037, SPEC-040]
solid-description: Contract for materializing one executable step instance from runtime context.
"""
class StepInstanceBuilding(Protocol):
    def build(
        self,
        step: StepDef,
        context: WorkflowRunContext,
        item: object,
        instance_id: str,
        iteration_index: int | None = None,
    ) -> StepInstance: ...

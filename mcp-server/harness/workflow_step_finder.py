"""Finds a resolved workflow step by identity."""

from __future__ import annotations

from typing import Protocol

from harness.flow_def import FlowDef
from harness.step_def import StepDef


"""
solid-name: WorkflowStepFinding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for resolving a step identity from a validated workflow definition.
"""
class WorkflowStepFinding(Protocol):
    def find(self, flow: FlowDef, step_id: str) -> StepDef: ...


"""
solid-name: WorkflowStepFinder
solid-category: service
solid-spec: [SPEC-045]
solid-description: Resolves a step identity from an already validated workflow definition.
"""
class WorkflowStepFinder(WorkflowStepFinding):
    def find(self, flow: FlowDef, step_id: str) -> StepDef:
        for step in flow.steps:
            if step.id == step_id:
                return step
        raise ValueError(
            f"Ready step '{step_id}' is absent from workflow '{flow.workflow_id}'"
        )

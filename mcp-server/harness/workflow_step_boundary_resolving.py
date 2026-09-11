"""Declares workflow-step boundary resolution."""

from __future__ import annotations

from typing import Protocol

from harness.flow_def import FlowDef
from harness.step_def import StepDef


"""
solid-name: WorkflowStepBoundaryResolving
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for identifying the workflow boundary that owns a resolved step.
"""
class WorkflowStepBoundaryResolving(Protocol):
    def resolve(self, flow: FlowDef, step: StepDef) -> str: ...

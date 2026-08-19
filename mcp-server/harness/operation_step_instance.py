"""Defines one executable internal operation instance."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.step_instance import StepInstance
from harness.workflow_context_values import WorkflowContextValues


"""
solid-name: OperationStepInstance
solid-category: model
solid-spec: [SPEC-010, SPEC-040]
solid-description: Carries typed resolved inputs required only by internal operation execution.
"""
@dataclass(frozen=True)
class OperationStepInstance(StepInstance):
    inputs: WorkflowContextValues[object] = field(
        default_factory=WorkflowContextValues
    )

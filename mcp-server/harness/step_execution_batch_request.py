"""Carries one correlated engine-owned workflow-step execution batch."""

from __future__ import annotations

from dataclasses import dataclass

from harness.models import StepDef
from harness.ready_step_execution_request import ReadyStepExecutionRequest
from harness.step_instance_execution import StepInstanceExecution


"""
solid-name: StepExecutionBatchRequest
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries ready-run context, one workflow step, and its correlated instance executions.
"""
@dataclass(frozen=True)
class StepExecutionBatchRequest:
    ready_request: ReadyStepExecutionRequest
    step_def: StepDef
    executions: list[StepInstanceExecution]

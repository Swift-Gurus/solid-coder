"""Defines typed process execution resolution for workflow steps."""

from typing import Protocol

from harness.process_execution import ProcessExecution
from harness.step_def import StepDef


"""
solid-name: StepProcessExecutionResolving
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for selecting a typed process execution request from a validated workflow step.
"""
class StepProcessExecutionResolving(Protocol):
    def resolve(self, step: StepDef) -> ProcessExecution: ...

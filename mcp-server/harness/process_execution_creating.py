"""Defines typed process execution creation for workflow steps."""

from typing import Protocol

from harness.process_execution import ProcessExecution
from harness.step_def import StepDef


"""
solid-name: ProcessExecutionCreating
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for creating a typed process execution request from a validated workflow step.
"""
class ProcessExecutionCreating(Protocol):
    def create(self, step: StepDef) -> ProcessExecution: ...

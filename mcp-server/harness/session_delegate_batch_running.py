"""Defines concurrent execution of ready session-delegate instances."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepInstance
from harness.step_instance_execution import StepInstanceExecution


"""
solid-name: SessionDelegateBatchRunning
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for executing a batch of session-delegate workflow instances.
"""
class SessionDelegateBatchRunning(Protocol):
    def run(
        self,
        instances: list[StepInstance],
    ) -> list[StepInstanceExecution]: ...

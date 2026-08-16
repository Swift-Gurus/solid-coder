"""Defines execution of one session-delegate workflow instance."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepInstance
from harness.step_instance_execution import StepInstanceExecution


"""
solid-name: SessionDelegateInstanceRunning
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for executing one session-delegate instance and correlating its outcome.
"""
class SessionDelegateInstanceRunning(Protocol):
    def run(self, instance: StepInstance) -> StepInstanceExecution: ...

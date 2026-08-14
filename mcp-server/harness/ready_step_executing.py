"""Defines execution of one ready workflow-step instance."""

from __future__ import annotations

from typing import Protocol

from harness.ready_step_execution_outcome import ReadyStepExecutionOutcome
from harness.ready_step_execution_request import ReadyStepExecutionRequest


"""
solid-name: ReadyStepExecuting
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-027]
solid-description: Contract for executing or recording one ready workflow-step instance.
"""
class ReadyStepExecuting(Protocol):
    def execute(
        self,
        request: ReadyStepExecutionRequest,
    ) -> ReadyStepExecutionOutcome: ...

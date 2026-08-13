"""Defines execution of typed workflow process requests."""

from __future__ import annotations

from typing import Protocol

from harness.process_execution import ProcessExecution
from harness.script_execution_result import ScriptExecutionResult


"""
solid-name: ProcessExecutionRunning
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for running a typed workflow process request with an explicit timeout.
"""
class ProcessExecutionRunning(Protocol):
    def run(
        self,
        execution: ProcessExecution,
        timeout_seconds: int | None,
    ) -> ScriptExecutionResult: ...

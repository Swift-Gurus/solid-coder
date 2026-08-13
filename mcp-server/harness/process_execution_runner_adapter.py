"""Adapts typed process requests to the existing subprocess runner."""

from __future__ import annotations

from harness.process_execution import ProcessExecution
from harness.script_execution_result import ScriptExecutionResult
from script_command_running import ScriptCommandRunning


"""
solid-name: ProcessExecutionRunnerAdapter
solid-category: adapter
solid-spec: [SPEC-027, SPEC-035]
solid-description: Runs typed workflow process requests through the established subprocess execution boundary.
"""
class ProcessExecutionRunnerAdapter:
    def __init__(self, runner: ScriptCommandRunning) -> None:
        self._runner = runner

    def run(
        self,
        execution: ProcessExecution,
        timeout_seconds: int | None,
    ) -> ScriptExecutionResult:
        return self._runner.run(execution.process_arguments(), timeout_seconds)

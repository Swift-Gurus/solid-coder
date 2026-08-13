"""Selects typed process execution for validated workflow steps."""

from harness.process_execution import ProcessExecution
from harness.process_execution_creating import ProcessExecutionCreating
from harness.step_def import StepDef


"""
solid-name: StepProcessExecutionResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Selects a typed process execution request from validated workflow steps.
"""
class StepProcessExecutionResolver:
    def __init__(self, execution_factory: ProcessExecutionCreating) -> None:
        self._execution_factory = execution_factory

    def resolve(self, step: StepDef) -> ProcessExecution:
        return self._execution_factory.create(step)

"""Creates typed process executions from validated workflow steps."""

from pathlib import Path
from typing import cast

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.inline_command_execution import InlineCommandExecution
from harness.legacy_script_execution import LegacyScriptExecution
from harness.process_execution import ProcessExecution
from harness.script_file_execution import ScriptFileExecution
from harness.step_def import StepDef


"""
solid-name: ProcessExecutionFactory
solid-category: factory
solid-spec: [SPEC-027, SPEC-035]
solid-description: Translates validated workflow steps into executable process requests.
"""
class ProcessExecutionFactory:
    _DEFAULT_EXECUTOR = "bash"

    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def create(self, step: StepDef) -> ProcessExecution:
        if step.script_file is not None:
            return ScriptFileExecution(
                executor=step.executor or self._DEFAULT_EXECUTOR,
                script_file=Path(step.script_file),
                arguments=step.args or [],
            )
        if step.type == "command":
            return InlineCommandExecution(
                executor=step.executor or self._DEFAULT_EXECUTOR,
                command=cast(str, step.command),
            )
        if step.type == "script":
            return LegacyScriptExecution(
                arguments=cast(list[str], step.command),
            )
        raise self._error_factory.create(
            f"Step '{step.id}' is not a process-execution step"
        )

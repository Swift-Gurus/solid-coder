"""Executes and validates Codex commands."""

from codex_execution_validating import CodexExecutionValidating
from subprocess_running import SubprocessRunning


"""
solid-name: CodexCommandExecutor
solid-category: service
solid-description: Executes Codex commands and validates their process outcomes.
solid-tags: [hook, llm]
"""
class CodexCommandExecutor:
    def __init__(
        self,
        subprocess_runner: SubprocessRunning,
        execution_validator: CodexExecutionValidating,
    ) -> None:
        self._subprocess_runner = subprocess_runner
        self._execution_validator = execution_validator

    def execute(
        self,
        command: list[str],
        timeout: int,
        stdin: object,
        cwd: str,
    ) -> None:
        succeeded, stdout, stderr = self._subprocess_runner.run(
            command,
            timeout=timeout,
            stdin=stdin,
            cwd=cwd or None,
        )
        self._execution_validator.validate(succeeded, stdout, stderr)

"""Executes validated read-only Git queries."""

from pathlib import Path

from harness.process_execution_running import ProcessExecutionRunning
from source.git_process_execution import GitProcessExecution
from source.git_querying import GitQuerying
from source.source_operation_error import SourceOperationError


"""
solid-name: GitQueryExecutor
solid-category: service
solid-spec: [SPEC-040]
solid-description: Executes read-only Git queries and reports failures with project and purpose context.
"""
class GitQueryExecutor(GitQuerying):
    def __init__(
        self,
        runner: ProcessExecutionRunning,
    ) -> None:
        self._runner = runner

    def query(
        self,
        project_root: Path,
        execution: GitProcessExecution,
        purpose: str,
    ) -> str:
        result = self._runner.run(
            execution,
            timeout_seconds=None,
            working_directory=str(project_root),
        )
        if result.exit_code != 0:
            raise SourceOperationError(
                f"Git query failed for '{project_root}' while {purpose}: "
                f"{result.stderr.strip()}"
            )
        return result.stdout

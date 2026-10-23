"""
solid-name: SubprocessScriptRunner
solid-category: service
solid-spec: [SPEC-027]
solid-description: Executes subprocess commands with timeout support and returns their exit code and captured output.
"""

from __future__ import annotations

import subprocess

from harness.script_execution_result import ScriptExecutionResult


class SubprocessScriptRunner:
    def run(
        self,
        command: list[str],
        timeout_seconds: int | None = None,
        stdin=None,
        cwd: str | None = None,
    ) -> ScriptExecutionResult:
        kwargs: dict = {}
        if stdin is not None:
            kwargs["stdin"] = stdin
        if cwd is not None:
            kwargs["cwd"] = cwd
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                **kwargs,
            )
            return ScriptExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ScriptExecutionResult(
                exit_code=None,
                stdout=self._decode(exc.stdout),
                stderr=self._decode(exc.stderr),
                timed_out=True,
            )

    def _decode(self, value) -> str:
        return value.decode() if isinstance(value, bytes) else (value or "")

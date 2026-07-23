"""
solid-name: ScriptExecutionResult
solid-category: model
solid-spec: [SPEC-027]
solid-description: Represents the outcome of a script command execution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScriptExecutionResult:
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool

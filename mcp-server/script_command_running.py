"""
solid-name: ScriptCommandRunning
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for executing a command with an explicit timeout.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Protocol

if TYPE_CHECKING:
    from harness.script_execution_result import ScriptExecutionResult


class ScriptCommandRunning(Protocol):

    def run(self, command: list[str], timeout_seconds: Optional[int]) -> "ScriptExecutionResult": ...

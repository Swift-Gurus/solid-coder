"""
solid-description: Contract for executing a shell command with configurable timeout and I/O, returning captured output.
solid-category: abstraction
"""

from typing import Protocol


class SubprocessRunning(Protocol):
    """Protocol for executing a shell command and returning captured output."""

    def run(
        self, cmd: list, timeout: int | None = None, stdin=None, cwd: str | None = None
    ) -> tuple: ...

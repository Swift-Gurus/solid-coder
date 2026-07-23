"""
solid-description: Contract for executing a shell command with configurable timeout and I/O, returning captured output.
solid-category: abstraction
"""

from typing import Optional, Protocol


class SubprocessRunning(Protocol):
    """Protocol for executing a shell command and returning captured output."""

    def run(self, cmd: list, timeout: Optional[int] = None, stdin=None, cwd: Optional[str] = None) -> tuple: ...
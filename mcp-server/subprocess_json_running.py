"""
solid-description: Contract for executing a shell command and returning parsed JSON output.
solid-category: abstraction
"""

from typing import Protocol


class SubprocessJsonRunning(Protocol):
    """Protocol for executing a shell command and returning parsed JSON output.

    Kept distinct from its sole production conformer (SubprocessJsonRunner in
    subprocess_adapter.py) so callers (run_gateway_cmd, run_claude_bare) and
    their tests can inject any duck-typed fake runner without depending on
    the concrete boundary adapter.
    """

    def run(
        self, cmd: list, timeout: int | None = None, stdin=None, cwd: str | None = None
    ) -> object: ...

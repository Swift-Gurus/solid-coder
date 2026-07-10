"""
solid-description: Contract for executing a shell command and returning parsed JSON output.
solid-category: abstraction
"""

from typing import Optional, Protocol


class SubprocessJsonRunning(Protocol):
    """Protocol for executing a shell command and returning parsed JSON output.

    Kept distinct from its sole production conformer (SubprocessJsonRunner in
    subprocess_adapter.py) so callers (run_gateway_cmd, run_claude_bare) and
    their tests can inject any duck-typed fake runner without depending on
    the concrete boundary adapter.
    """

    def run(self, cmd: list, timeout: Optional[int] = None, stdin=None, cwd: Optional[str] = None) -> object: ...
"""
solid-description: Executes a subprocess command and returns its success status and captured output.
solid-category: service
solid-tags: [hook]
"""

import subprocess
from typing import Optional

from hook_utils import SubprocessError


class SubprocessAdapter:
    """Boundary adapter: wraps subprocess.run for injection.

    subprocess.run is a global stdlib function (not developer-owned, cannot be
    subclassed) — this adapter satisfies the OCP Boundary Adapter exception.
    Kept independent of the flow engine's SubprocessScriptRunner: this module is
    imported by core hook infrastructure repo-wide and must not depend on the
    harness package.
    """

    def run(self, cmd: list, timeout: Optional[int] = None, stdin=None, cwd: Optional[str] = None) -> tuple:
        kwargs: dict = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if stdin is not None:
            kwargs["stdin"] = stdin
        if cwd is not None:
            kwargs["cwd"] = cwd
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            raise SubprocessError(f"`{cmd[0]}` timed out after {timeout}s")

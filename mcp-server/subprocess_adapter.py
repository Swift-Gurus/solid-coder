"""
solid-description: Executes system commands with error handling and optional JSON parsing of results.
solid-category: service
solid-tags: [hook]
"""

import json
import subprocess
from typing import Optional

from hook_utils import SubprocessError, SubprocessRunning


class SubprocessAdapter:
    """Boundary adapter: wraps subprocess.run for injection.

    subprocess.run is a global stdlib function (not developer-owned, cannot be
    subclassed) — this adapter satisfies the OCP Boundary Adapter exception.
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


class SubprocessJsonRunner:
    """Runs a subprocess command and parses stdout as JSON.

    Reuses SubprocessRunning for execution; adds JSON parsing and error raising.
    """

    def __init__(self, runner: SubprocessRunning) -> None:
        self._runner = runner

    def run(self, cmd: list, timeout: Optional[int] = None, stdin=None, cwd: Optional[str] = None) -> object:
        runner_kwargs: dict = {"timeout": timeout, "stdin": stdin}
        if cwd is not None:
            runner_kwargs["cwd"] = cwd
        try:
            success, stdout, stderr = self._runner.run(cmd, **runner_kwargs)
        except SubprocessError:
            raise
        except Exception as exc:
            raise SubprocessError(f"`{cmd[0]}` failed: {exc}")
        if not success:
            label = " ".join(cmd[:2])
            raise SubprocessError(
                f"`{label}` exited with error" + (f":\n{stderr}" if stderr else "")
            )
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise SubprocessError(f"`{cmd[0]}` produced invalid JSON: {exc}")
